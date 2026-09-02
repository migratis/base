"""One generic client, and the envelope that makes it safe to point at a URL a
user chose.

SCOPE_external_data_sources.md@d2de531 §8.1, and **D1**: Migratis ships no
provider code. There is no TMDB module, no IMDb client, no per-provider Python
anywhere — an adapter is rows in a table reached by this file, which is what
makes shipping a dozen of them a cost of *checking whether a URL still works*
rather than of keeping twelve integrations alive.

`routing/views.py` could state *"the engine URL comes from settings and never
from the request (no SSRF)"*. This feature breaks that premise on purpose, so it
replaces it with an envelope rather than inheriting a promise it cannot keep:

1. **https only, no userinfo** — refused before a socket exists (`generator`'s
   shape module at declaration time, re-checked here at call time, because a
   catalog snapshot is immutable and a stored row is not).
2. **The deny policy** (§8.1a), asked on **every** call so a host denied this
   afternoon stops working this afternoon.
3. **Every resolved address checked**, and the connection then **pinned to the
   address that was checked** — `PinnedHTTPAdapter` connects to the validated IP
   with SNI and certificate verification still against the real hostname, and
   the `Host` header preserved. The cheap alternative — reading the peer address
   off the socket after connect and discarding the response if it is private —
   leaves a request already sent to an internal service. This is the main
   implementation risk in the scope and the one place to spend care.
4. **No redirects followed.** A 3xx is an error the adapter must fix; chasing one
   re-opens every check above at a hop nobody validated.
5. **A response ceiling**: connect and read timeouts, a byte cap read
   *incrementally* (never `len(response.content)` after the fact), a JSON
   content type required, and a parse depth cap.
6. **Nothing of Migratis' rides along**: no session cookie, no PAT, no
   `X-Agent-Identity`, no `Referer`, no `User-Agent` naming a customer. The only
   header is the declared one.

**GET only, in any version** (D9). A primitive that can POST to a third party is
a webhook system, has entirely different failure and abuse properties, and is
not this.
"""
import json
import logging
import socket
from urllib.parse import quote, urlencode, urlsplit

import requests
from requests.adapters import HTTPAdapter

from . import addresses, policy
from .hosts import normalise_host

logger = logging.getLogger(__name__)

CONNECT_TIMEOUT = 5
READ_TIMEOUT    = 12
MAX_BYTES       = 512 * 1024      # a search page, not a dataset
MAX_DEPTH       = 12
# Deliberately anonymous. It names the software and nothing about the caller,
# the application or the deployment — a User-Agent is the easiest place for a
# customer's identity to leak to a third party nobody vetted.
USER_AGENT = 'Migratis-DataSource/1.0'


class DataSourceError(Exception):
    """Base. Never rendered at a user without one of the two names below."""


class SourceUnavailable(DataSourceError):
    """Unreachable, 5xx, timeout, malformed body, or a refusal of ours.

    §8.4 — the form keeps what the user typed and badges the button. **Never a
    silent empty list.**
    """


class SourceRefused(DataSourceError):
    """401 / 403 / 429 from the source. The owner's problem, said as such.

    Carries the status so the message can name it; the key is never echoed.
    """

    def __init__(self, message='', status=None):
        super().__init__(message)
        self.status = status


class PinnedHTTPAdapter(HTTPAdapter):
    """Connect to the address we validated, prove the certificate of the name.

    The request URL is rewritten to the IP so urllib3 opens the socket there;
    `assert_hostname` keeps certificate verification against the real hostname
    and `server_hostname` keeps SNI correct, so a pinned connection is exactly as
    authenticated as an unpinned one. Without both, pinning would trade an SSRF
    for a TLS hole, which is not a trade.
    """

    def __init__(self, hostname, **kwargs):
        self._pinned_hostname = hostname
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs['assert_hostname'] = self._pinned_hostname
        conn_kw = dict(kwargs.get('conn_kw') or {})
        conn_kw['server_hostname'] = self._pinned_hostname
        kwargs['conn_kw'] = conn_kw
        return super().init_poolmanager(*args, **kwargs)


def _pinned_url(url, ip):
    """`url` with its host replaced by one validated address, port preserved."""
    parts = urlsplit(url)
    host = f'[{ip}]' if ':' in ip else ip
    netloc = f'{host}:{parts.port}' if parts.port else host
    return parts._replace(netloc=netloc).geturl()


def build_request(adapter, *, path, params=None, credential=''):
    """`(url, params, headers)` for one call, built from the STORED adapter.

    Nothing from a request body reaches this except the search text, which
    travels as a *parameter value* and is never interpolated into a path or a
    host (§4.1 step 3).
    """
    base = (adapter.base_url or '').rstrip('/')
    url = f'{base}{path}'
    query = dict(params or {})
    headers = {
        'Accept': 'application/json',
        'User-Agent': USER_AGENT,
        # An explicit close: a pooled connection to a user-declared host is a
        # socket held open to somewhere nobody vetted.
        'Connection': 'close',
    }
    mode = (adapter.auth_mode or 'none').strip()
    name = (adapter.auth_name or '').strip()
    if credential and name:
        if mode == 'header':
            headers[name] = credential
        elif mode == 'query':
            query[name] = credential
    return url, query, headers


def fetch_json(adapter, *, path, params=None, credential=''):
    """One GET through the whole envelope. Raises `SourceUnavailable` /
    `SourceRefused`, never returns a partial answer."""
    url, query, headers = build_request(adapter, path=path, params=params,
                                        credential=credential)
    parts = urlsplit(url)
    if parts.scheme != 'https':
        raise SourceUnavailable('scheme-refused')
    hostname = normalise_host(parts.hostname or '')
    if not hostname:
        raise SourceUnavailable('no-host')
    if parts.username or parts.password:
        raise SourceUnavailable('userinfo-refused')
    # Asked on EVERY call, not only at the gate: a host that becomes a problem
    # after approval must stop working without anyone re-saving a row (§8.1a).
    if not policy.host_allowed(hostname):
        raise SourceUnavailable('host-denied')

    port = parts.port or 443
    try:
        resolved = addresses.resolve_public(hostname, port)
    except addresses.AddressRefused as exc:
        raise SourceUnavailable(str(exc)) from exc

    last = None
    for _family, ip in resolved:
        try:
            return _send(url, ip, hostname, query, headers)
        except SourceRefused:
            raise
        except SourceUnavailable as exc:
            last = exc
            continue
    raise last or SourceUnavailable('unreachable')


def _send(url, ip, hostname, query, headers):
    session = requests.Session()
    # A fresh session with nothing carried over. `trust_env` off is what stops a
    # deployment's own proxy variables and netrc credentials riding out to a host
    # the owner declared (§8.1 item 6).
    session.trust_env = False
    session.headers.clear()
    session.max_redirects = 0
    session.mount('https://', PinnedHTTPAdapter(hostname, max_retries=0))
    request_headers = dict(headers)
    request_headers['Host'] = hostname
    target = _pinned_url(url, ip)
    if query:
        target = f'{target}{"&" if urlsplit(target).query else "?"}{urlencode(query, doseq=False)}'
    try:
        response = session.get(
            target, headers=request_headers, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            allow_redirects=False, stream=True,
        )
    except requests.exceptions.RequestException as exc:
        raise SourceUnavailable(f'transport:{type(exc).__name__}') from exc
    finally:
        pass

    try:
        return _read(response)
    finally:
        response.close()
        session.close()


def _read(response):
    status = response.status_code
    if status in (401, 403, 429):
        # The owner's problem, said as such (§8.4). The provider's body is
        # dropped: it is where an API key and an account state get quoted.
        raise SourceRefused('refused', status=status)
    if 300 <= status < 400:
        raise SourceUnavailable('redirect-refused')
    if status >= 400:
        raise SourceUnavailable(f'status:{status}')

    content_type = (response.headers.get('Content-Type') or '').split(';')[0].strip().lower()
    if content_type and not (content_type == 'application/json' or
                             content_type.endswith('+json')):
        # JSON only (§13). An HTML error page that parses as nothing is a
        # different failure from a source with no results, and conflating them is
        # how "the API returned nothing" becomes the answer to "your key expired".
        raise SourceUnavailable(f'content-type:{content_type}')

    body = bytearray()
    for chunk in response.iter_content(8192):
        body.extend(chunk)
        if len(body) > MAX_BYTES:
            # Incrementally, never `len(response.content)` after the fact — by
            # then the ceiling has already been exceeded in memory, which is the
            # thing the ceiling exists to prevent.
            raise SourceUnavailable('too-large')
    try:
        payload = json.loads(bytes(body).decode('utf-8', errors='replace'))
    except (ValueError, UnicodeDecodeError) as exc:
        raise SourceUnavailable('not-json') from exc
    if _depth(payload) > MAX_DEPTH:
        raise SourceUnavailable('too-deep')
    return payload


def _depth(value, level=1):
    """How deep a parsed payload nests. A cheap ceiling on a document somebody
    else composed — the parse itself is bounded by MAX_BYTES, this bounds what
    the mapper then walks."""
    if level > MAX_DEPTH + 1:
        return level
    if isinstance(value, dict):
        return max((_depth(v, level + 1) for v in value.values()), default=level)
    if isinstance(value, list):
        return max((_depth(v, level + 1) for v in value[:200]), default=level)
    return level


def search_path_for(adapter, query_text):
    """The search request's path and params. The user's text is a VALUE."""
    return adapter.search_path, {adapter.query_param or 'q': query_text}


def detail_path_for(adapter, external_id):
    """`detail_path` with its single `{id}` substituted, percent-encoded.

    The substitution is a templating language of exactly one variable,
    deliberately (§4.2) — and the value is quoted with no safe characters, so an
    identifier a provider handed back cannot climb out of the path it was
    substituted into.
    """
    return (adapter.detail_path or '').replace('{id}', quote(str(external_id), safe=''))
