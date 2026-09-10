"""A lookup, end to end — and the one sentence that makes the feature safe.

    **An external source fills a form; it never writes a row.**

SCOPE_external_data_sources.md@d2de531 §4. A lookup returns *candidate values*;
a human or an end user picks one; the record is then created by the ordinary
write path that already exists, with its required-field check, its role gate,
its computed fields, its geo and numeric normalisation and its row-visibility
rule all intact. A source that could write a row by itself would be a second
write path past all five — the argument `SCOPE_data_export.md@dbaa37a` already
made against a server-side exporter, in the opposite direction.

Nothing here is billed. No AI provider is reached by a lookup, an adoption or a
probe, so this module goes nowhere near `ai_debit_credits` and nowhere near
`credits.services` (**D6**), and a test reads its source for those names exactly
as `routing/views.py` already has one.
"""
import base64
import logging

from . import breaker, client, mapping, throttle

logger = logging.getLogger(__name__)

# How many media files one PICK may fetch. A binding is free to map five image
# fields, and a user who clicks "use this" made one choice, not five requests.
MAX_INLINE_MEDIA = 2

# The field types whose value is a FILE rather than a reference to one. Only
# `image` for now: an arbitrary `file` slot would mean fetching whatever a
# payload names with no way to say what a legitimate answer looks like, and
# nobody has asked for one.
MEDIA_FIELD_TYPES = ('image',)

# The three outcomes §8.4 tells apart, because the caller does something
# different with each. They are i18n keys: the frontend renders them, and a
# quota stop must NEVER arrive as an empty candidate list.
UNAVAILABLE      = 'datasource-unavailable'
REFUSED          = 'datasource-refused'
QUOTA_EXHAUSTED  = 'datasource-quota-exhausted'


class LookupError_(Exception):
    """A named failure. `key` is what the UI renders; `status` rides along on a
    refusal so the owner is told *which* refusal it was."""

    def __init__(self, key, status=None):
        super().__init__(key)
        self.key = key
        self.status = status


def _guard(application_id, adapter):
    """The order that matters (§8.3): a breaker that is open costs nothing, so it
    is asked before the meter is spent."""
    scope = breaker.scope_key(application_id, adapter.slug)
    if breaker.is_tripped(scope):
        raise LookupError_(UNAVAILABLE)
    if not throttle.consume_daily(application_id):
        # Never "no results". An empty list that actually means *you have run
        # out* is the route-not-found-vs-engine-unavailable mistake in a new
        # module.
        raise LookupError_(QUOTA_EXHAUSTED)
    return scope


def _call(scope, adapter, *, path, params=None, credential=''):
    try:
        return client.fetch_json(adapter, path=path, params=params, credential=credential)
    except client.SourceRefused as exc:
        # 401/403/429 all morning is a dead key, and every retry is a row on the
        # owner's bill. Stop calling.
        breaker.trip(scope, f'refused:{exc.status}')
        raise LookupError_(REFUSED, status=exc.status) from exc
    except client.SourceUnavailable as exc:
        reason = str(exc)
        # A refusal of *ours* — a denied host, a private address, a scheme — is
        # not a flaky source and must not be forgotten in five minutes; a
        # transport failure is, and tripping on one would take a source away over
        # a single lost packet.
        if reason in ('host-denied', 'private-address', 'scheme-refused',
                      'userinfo-refused', 'no-host', 'redirect-refused'):
            breaker.trip(scope, reason)
        raise LookupError_(UNAVAILABLE) from exc


def search(adapter, binding, query_text, *, credential='', application_id=None):
    """`[{label, id, values}]` — the one-step flow (§4.1).

    `values` is already this application's field names, because the two hops run
    back to back here: the adapter's `provides` resolves the payload into slots,
    and the binding's `field_map` resolves slots into fields. Nothing is written.
    """
    scope = _guard(application_id, adapter)
    path, params = client.search_path_for(adapter, (query_text or '').strip())
    payload = _call(scope, adapter, path=path, params=params, credential=credential)
    candidates = []
    for entry in mapping.resolve_slots(payload, adapter):
        candidates.append({
            'label':  entry['label'],
            'id':     entry['id'],
            'values': mapping.bind_values(entry['slots'], binding),
        })
    return candidates


def inline_media_values(values, binding, *, max_media=MAX_INLINE_MEDIA):
    """A URL bound to an `image` field, replaced by the bytes it names.

    Prod app 8: a poster URL fills the form, `ImageField` previews it, the save
    reports success and **no image is stored** — the emitted service appends the
    URL as a plain string and the view's `UploadedFile = File(None)` never sees
    a file. `ai_sandbox_config` already states the shape an `image` value has to
    have, and it is the one an uploaded file already produces:
    `"data:image/jpeg;base64,…"`. So the fix is to deliver that shape, not to
    teach four write paths to recognise a URL.

    Keyed on the target field's **declared type**, the mapper's rule
    throughout: a `string` field holding a URL is a URL, and fetching it would
    be inventing a file nobody declared.

    A fetch that fails leaves the field **absent, never the URL**. The URL is
    precisely the thing that cannot be stored, and leaving it is what made the
    form show a poster the save then dropped — a success message over a missing
    image. Absent lets the ordinary required check speak instead, which is the
    same judgement `resolve_path` makes about a path that does not resolve.

    Not billed and not metered: the daily ceiling was consumed by the lookup
    this belongs to, and a CDN that is down must not trip the API's breaker.
    """
    fetched = 0
    for field_name, slot_type in sorted((binding.field_types or {}).items()):
        if slot_type not in MEDIA_FIELD_TYPES:
            continue
        value = values.get(field_name)
        if not isinstance(value, str) or not value.startswith('https://'):
            continue
        if fetched >= max_media:
            values.pop(field_name, None)
            continue
        fetched += 1
        try:
            content_type, blob = client.fetch_binary(value)
        except client.DataSourceError as exc:
            logger.info('[DATASOURCE] media not inlined for %s: %s', field_name, exc)
            values.pop(field_name, None)
            continue
        encoded = base64.b64encode(blob).decode('ascii')
        values[field_name] = f'data:{content_type};base64,{encoded}'
    return values


def detail(adapter, binding, external_id, *, credential='', application_id=None,
           inline_media=False):
    """The second request of the two-step flow, fired on the PICK (§4.2).

    OMDb answers a search with ids and needs `?i=<id>` for the fields; TMDB wants
    `/movie/{id}` for credits. A one-step-only primitive does not serve the case
    that triggered this scope, which is why `detail_path` is in v1 — two
    requests, one user action.

    `inline_media` is off by default and asked for by **a generated
    application's lookup only**. The design sandbox stores its records as JSON,
    so a poster URL renders there and is left exactly as the provider sent it —
    which keeps a designer's preview talking to the one host they declared,
    rather than to whatever host that host's payload names. It rides on the
    PICK rather than on the search because a search answers up to
    `MAX_CANDIDATES` results and nobody chose any of them yet.
    """
    if not (adapter.detail_path or '').strip():
        raise LookupError_(UNAVAILABLE)
    scope = _guard(application_id, adapter)
    path = client.detail_path_for(adapter, external_id)
    payload = _call(scope, adapter, path=path, credential=credential)
    # A detail endpoint answers ONE object, not a list — but a provider that
    # wraps it in its own `result_path` is common enough (OMDb does not, Open
    # Library does) that the list reading is tried first and the object is the
    # fallback rather than the other way round.
    listed = mapping.result_list(payload, adapter)
    item = listed[0] if listed else (payload if isinstance(payload, dict) else {})
    slots = mapping.slots_of(item, adapter)
    values = mapping.bind_values(slots, binding)
    if inline_media:
        inline_media_values(values, binding)
    return {
        'label':  mapping._text(mapping.resolve_path(item, adapter.label_path)),
        'id':     str(external_id),
        'values': values,
    }


def probe(adapter, *, credential='', application_id=None, query_text='test'):
    """§5.4 item 3 — one real search against the live endpoint.

    Returns `(ok, detail)`. `result_path` must resolve to a list, and at least
    one declared slot must resolve inside its first element; anything less and
    the adapter would look like an API with no data forever.

    **We check it resolves, you check it is the right data.** The lookup preview
    is the verdict, and it is the whole reason a human lane can be trusted with a
    primitive that reaches the network.
    """
    scope = breaker.scope_key(application_id, adapter.slug)
    try:
        payload = _call(scope, adapter,
                        path=client.search_path_for(adapter, query_text)[0],
                        params=client.search_path_for(adapter, query_text)[1],
                        credential=credential)
    except LookupError_ as exc:
        return False, {'code': exc.key, 'status': exc.status}
    listed = mapping.result_list(payload, adapter)
    if not isinstance(listed, list) or not listed:
        return False, {'code': 'probe_no_results'}
    first = listed[0] if isinstance(listed[0], dict) else {}
    slots = mapping.slots_of(first, adapter)
    if not slots:
        return False, {'code': 'probe_no_slot_resolved'}
    return True, {
        'label': mapping._text(mapping.resolve_path(first, adapter.label_path)),
        'slots': slots,
        'count': len(listed),
    }
