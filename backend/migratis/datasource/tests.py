"""SCOPE_external_data_sources.md@d2de531 P1 — the module and its envelope.

`routing/views.py` could state its own premise: *"the engine URL still comes
from settings and never from the request (no SSRF)."* This feature breaks that
premise on purpose, so the tests here are not a formality — they are the reason
the feature can ship.

Everything runs against a **local stub server** rather than a mock, because the
thing under test is what happens on a socket: a redirect, a content type, a body
that never ends, a hostname that resolves somewhere it should not.
"""
import ipaddress
import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest import mock

from django.core.cache import cache
from django.test import TestCase, override_settings

from . import addresses, breaker, client, mapping, policy, services, throttle
from .hosts import host_matches, normalise_host
from .mapping import AdapterSpec, BindingSpec


# --------------------------------------------------------------------------- #
# A stub provider
# --------------------------------------------------------------------------- #

class _Handler(BaseHTTPRequestHandler):
    routes = {}

    def log_message(self, *args):        # keep the test output readable
        pass

    def do_GET(self):
        path = self.path.split('?')[0]
        spec = self.routes.get(path) or self.routes.get('*')
        if spec is None:
            self.send_response(404)
            self.end_headers()
            return
        status, content_type, body = spec(self) if callable(spec) else spec
        self.send_response(status)
        if content_type:
            self.send_header('Content-Type', content_type)
        if isinstance(body, str):
            body = body.encode()
        self.send_header('Content-Length', str(len(body)))
        if status in (301, 302, 303, 307, 308):
            self.send_header('Location', 'https://example.invalid/moved')
        self.end_headers()
        self.wfile.write(body)


class StubProvider:
    """An HTTP server on 127.0.0.1 — which the envelope refuses on principle, so
    every test that wants an answer pins the resolver at it explicitly."""

    def __init__(self, routes):
        _Handler.routes = routes
        self.server = HTTPServer(('127.0.0.1', 0), _Handler)
        self.port = self.server.server_port
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()


def _plain_send(url, ip, hostname, query, headers):
    """`client._send` over http against the stub.

    The TLS pinning it replaces is exercised by `PinnedHTTPAdapterTests`; this
    stands in for the transport so that the *envelope* — redirects, ceilings,
    content types, statuses — can be tested against a real socket without
    inventing a certificate authority in a unit test.
    """
    import requests
    from urllib.parse import urlencode, urlsplit
    target = url.replace('https://', 'http://')
    if query:
        target = f'{target}{"&" if urlsplit(target).query else "?"}{urlencode(query)}'
    response = requests.get(target, headers=headers, timeout=(2, 5),
                            allow_redirects=False, stream=True)
    try:
        return client._read(response)
    finally:
        response.close()


def adapter(**over):
    data = dict(slug='stub', base_url='https://provider.test', search_path='/search',
                query_param='q', result_path='results', label_path='title',
                id_path='id', provides={'title': 'title', 'year': 'year'})
    data.update(over)
    return AdapterSpec(**data)


# --------------------------------------------------------------------------- #
# §8.1 — where a packet is allowed to go
# --------------------------------------------------------------------------- #

class AddressRefusalTests(TestCase):
    """Every private-address refusal, one test each.

    Validating only when a row is saved is worthless: DNS answers can change
    between the save and the call, which is DNS rebinding stated as a sentence —
    so this runs at connect time, and it is why §5.4's probe is a gate and not a
    guarantee.
    """

    def test_loopback_is_refused(self):
        self.assertFalse(addresses.is_public('127.0.0.1'))

    def test_ipv6_loopback_is_refused(self):
        self.assertFalse(addresses.is_public('::1'))

    def test_rfc1918_is_refused(self):
        for ip in ('10.0.0.5', '172.16.0.1', '192.168.1.1'):
            self.assertFalse(addresses.is_public(ip), ip)

    def test_link_local_is_refused(self):
        self.assertFalse(addresses.is_public('169.254.1.1'))

    def test_the_cloud_metadata_endpoint_is_refused(self):
        """Already inside link-local, and written out anyway because it is *the*
        target — a future edit that loosens link-local must trip over it."""
        self.assertFalse(addresses.is_public('169.254.169.254'))

    def test_cgnat_is_refused(self):
        """Neither is_private nor is_reserved in the stdlib's reading, and on a
        good many hosts it is the provider's own network."""
        self.assertFalse(addresses.is_public('100.64.0.1'))

    def test_multicast_and_reserved_and_unspecified_are_refused(self):
        for ip in ('224.0.0.1', '240.0.0.1', '0.0.0.0'):
            self.assertFalse(addresses.is_public(ip), ip)

    def test_unique_local_ipv6_is_refused(self):
        self.assertFalse(addresses.is_public('fd00::1'))

    def test_an_ipv4_mapped_ipv6_loopback_is_refused(self):
        """The loopback wearing a different type. Unwrapped before every other
        test, or each one is asked about the wrong address."""
        self.assertFalse(addresses.is_public('::ffff:127.0.0.1'))

    def test_a_6to4_address_carrying_a_private_v4_is_refused(self):
        self.assertFalse(addresses.is_public('2002:7f00:0001::1'))

    def test_a_public_address_is_allowed(self):
        self.assertTrue(addresses.is_public('93.184.216.34'))
        self.assertTrue(addresses.is_public('2606:2800:220:1::1'))

    def test_a_literal_private_host_is_refused_without_dns(self):
        with self.assertRaises(addresses.AddressRefused):
            addresses.resolve_public('127.0.0.1')

    def test_all_answers_must_be_public_not_just_one(self):
        """A name answering with one routable address and one loopback is a
        rebinding attempt wearing a single DNS response; picking the good one
        would make the attack a matter of resolver ordering."""
        answers = [
            (socket.AF_INET, 1, 6, '', ('93.184.216.34', 443)),
            (socket.AF_INET, 1, 6, '', ('127.0.0.1', 443)),
        ]
        with mock.patch('socket.getaddrinfo', return_value=answers):
            with self.assertRaises(addresses.AddressRefused):
                addresses.resolve_public('rebind.test')

    def test_a_name_that_does_not_resolve_is_named_as_such(self):
        with mock.patch('socket.getaddrinfo', side_effect=socket.gaierror):
            with self.assertRaises(addresses.AddressRefused) as ctx:
                addresses.resolve_public('nowhere.test')
        self.assertEqual(str(ctx.exception), 'dns-failed')


class PinnedHTTPAdapterTests(TestCase):
    """§8.1 — the connection must go to the address that was checked.

    The cheap alternative (read the peer address off the socket after connect and
    discard the response if it is private) leaves a request already sent to an
    internal service. Pinning must not trade an SSRF for a TLS hole either, so
    both halves are asserted: the socket goes to the IP, the certificate is still
    proved against the name.
    """

    def test_the_pool_verifies_the_real_hostname(self):
        pinned = client.PinnedHTTPAdapter('api.example.com')
        pool_kw = pinned.poolmanager.connection_pool_kw
        self.assertEqual(pool_kw['assert_hostname'], 'api.example.com')
        self.assertEqual(pool_kw['conn_kw']['server_hostname'], 'api.example.com')

    def test_the_url_is_rewritten_to_the_validated_address(self):
        self.assertEqual(client._pinned_url('https://api.example.com/3/search', '1.2.3.4'),
                         'https://1.2.3.4/3/search')

    def test_a_port_survives_the_rewrite(self):
        self.assertEqual(client._pinned_url('https://api.example.com:8443/x', '1.2.3.4'),
                         'https://1.2.3.4:8443/x')

    def test_an_ipv6_address_is_bracketed(self):
        self.assertEqual(client._pinned_url('https://api.example.com/x', '2606::1'),
                         'https://[2606::1]/x')


class RequestBuildingTests(TestCase):
    """§8.1 item 6 — nothing of Migratis' rides along."""

    def test_only_the_declared_header_travels(self):
        _url, _q, headers = client.build_request(
            adapter(auth_mode='header', auth_name='Authorization'),
            path='/search', credential='secret-token')
        self.assertEqual(headers['Authorization'], 'secret-token')
        for forbidden in ('Cookie', 'Referer', 'X-Agent-Identity', 'Authorization-Bearer'):
            if forbidden != 'Authorization':
                self.assertNotIn(forbidden, headers)

    def test_a_bearer_token_travels_with_its_scheme(self):
        """The catalogue's TMDB adapter documented `Authorization: Bearer <token>`
        in its own changelog and nothing produced it — a pasted v4 read token went
        out bare, which is not a credentials scheme, and the source answered 401
        forever. The scheme belongs to the declaration, not to the secret."""
        _url, _q, headers = client.build_request(
            adapter(auth_mode='bearer', auth_name='Authorization'),
            path='/search', credential='eyJhbGci')
        self.assertEqual(headers['Authorization'], 'Bearer eyJhbGci')

    def test_a_token_already_carrying_the_scheme_is_not_prefixed_twice(self):
        """`Bearer Bearer …` is the shape of an owner who typed the workaround
        before the mode existed. Their stored key keeps working."""
        for stored in ('Bearer eyJhbGci', 'bearer eyJhbGci', '  Bearer   eyJhbGci  '):
            _url, _q, headers = client.build_request(
                adapter(auth_mode='bearer', auth_name='Authorization'),
                path='/search', credential=stored)
            self.assertEqual(headers['Authorization'], 'Bearer eyJhbGci')

    def test_header_mode_is_unchanged_and_sends_the_value_verbatim(self):
        """`X-Api-Key: <value>` is a legitimate declaration and must not acquire
        a scheme it never asked for."""
        _url, _q, headers = client.build_request(
            adapter(auth_mode='header', auth_name='X-Api-Key'),
            path='/search', credential='K')
        self.assertEqual(headers['X-Api-Key'], 'K')

    def test_the_user_agent_names_the_software_and_nothing_about_the_caller(self):
        _url, _q, headers = client.build_request(adapter(), path='/search')
        self.assertEqual(headers['User-Agent'], client.USER_AGENT)
        self.assertNotIn('migratis.ai', headers['User-Agent'])

    def test_a_query_mode_key_rides_as_a_parameter(self):
        _url, params, headers = client.build_request(
            adapter(auth_mode='query', auth_name='api_key'),
            path='/search', params={'q': 'dune'}, credential='K')
        self.assertEqual(params, {'q': 'dune', 'api_key': 'K'})
        self.assertNotIn('api_key', headers)

    def test_a_keyless_adapter_sends_no_key(self):
        _url, params, headers = client.build_request(adapter(), path='/search',
                                                     credential='ignored')
        self.assertEqual(params, {})
        self.assertEqual(set(headers), {'Accept', 'User-Agent', 'Connection'})

    def test_the_search_text_is_a_value_never_a_path(self):
        path, params = client.search_path_for(adapter(), '../../etc/passwd')
        self.assertEqual(path, '/search')
        self.assertEqual(params, {'q': '../../etc/passwd'})

    def test_an_identifier_cannot_climb_out_of_the_path_it_is_substituted_into(self):
        path = client.detail_path_for(adapter(detail_path='/movie/{id}'), '../admin')
        self.assertEqual(path, '/movie/..%2Fadmin')


# --------------------------------------------------------------------------- #
# The response ceiling, against a real socket
# --------------------------------------------------------------------------- #

class ResponseCeilingTests(TestCase):
    def _fetch(self, routes, path='/search'):
        """The stub answers on loopback, which the envelope refuses on principle
        — correctly, and `AddressRefusalTests` is what pins that. Here the
        address check is stood down explicitly so the *response* half can be
        tested against a real socket."""
        with StubProvider(routes) as stub:
            with mock.patch.object(client, '_send', _plain_send), \
                    mock.patch.object(client.addresses, 'resolve_public',
                                      return_value=[(socket.AF_INET, '127.0.0.1')]):
                return client.fetch_json(
                    adapter(base_url=f'https://127.0.0.1:{stub.port}'), path=path)

    def test_a_json_body_is_returned(self):
        payload = self._fetch({'/search': (200, 'application/json',
                                           json.dumps({'results': [{'title': 'Dune'}]}))})
        self.assertEqual(payload['results'][0]['title'], 'Dune')

    def test_a_redirect_is_an_error_the_adapter_must_fix(self):
        """Chasing one re-opens every check above at a hop nobody validated."""
        with self.assertRaises(client.SourceUnavailable) as ctx:
            self._fetch({'/search': (302, 'application/json', '{}')})
        self.assertEqual(str(ctx.exception), 'redirect-refused')

    def test_html_is_refused_rather_than_parsed_as_nothing(self):
        """An HTML error page that parses as nothing is a different failure from a
        source with no results, and conflating them is how "the API returned
        nothing" becomes the answer to "your key expired"."""
        with self.assertRaises(client.SourceUnavailable) as ctx:
            self._fetch({'/search': (200, 'text/html', '<html>nope</html>')})
        self.assertTrue(str(ctx.exception).startswith('content-type:'))

    def test_a_body_over_the_cap_is_refused_while_it_is_still_arriving(self):
        big = json.dumps({'results': [{'title': 'x' * 1000}] * 2000})
        self.assertGreater(len(big), client.MAX_BYTES)
        with self.assertRaises(client.SourceUnavailable) as ctx:
            self._fetch({'/search': (200, 'application/json', big)})
        self.assertEqual(str(ctx.exception), 'too-large')

    def test_a_body_that_is_not_json_is_named_as_such(self):
        with self.assertRaises(client.SourceUnavailable) as ctx:
            self._fetch({'/search': (200, 'application/json', 'not json at all')})
        self.assertEqual(str(ctx.exception), 'not-json')

    def test_a_deeply_nested_body_is_refused(self):
        deep = json.dumps(_nest(client.MAX_DEPTH + 4))
        with self.assertRaises(client.SourceUnavailable) as ctx:
            self._fetch({'/search': (200, 'application/json', deep)})
        self.assertEqual(str(ctx.exception), 'too-deep')

    def test_401_is_told_apart_from_unreachable(self):
        """§8.4 — the owner's problem, said as such, with the status; the key is
        never echoed."""
        with self.assertRaises(client.SourceRefused) as ctx:
            self._fetch({'/search': (401, 'application/json', '{"error":"bad key ABC123"}')})
        self.assertEqual(ctx.exception.status, 401)
        self.assertNotIn('ABC123', str(ctx.exception))

    def test_429_is_a_refusal_not_an_outage(self):
        with self.assertRaises(client.SourceRefused) as ctx:
            self._fetch({'/search': (429, 'application/json', '{}')})
        self.assertEqual(ctx.exception.status, 429)

    def test_a_5xx_is_an_outage(self):
        with self.assertRaises(client.SourceUnavailable):
            self._fetch({'/search': (503, 'application/json', '{}')})


def _nest(levels):
    value = {'leaf': 1}
    for _ in range(levels):
        value = {'x': value}
    return value


class SchemeAndHostRefusalTests(TestCase):
    def test_http_never_reaches_a_socket(self):
        with self.assertRaises(client.SourceUnavailable) as ctx:
            client.fetch_json(adapter(base_url='http://provider.test'), path='/search')
        self.assertEqual(str(ctx.exception), 'scheme-refused')

    @override_settings(DATASOURCE_HOST_POLICY='', DATASOURCE_DENIED_HOSTS='provider.test')
    def test_a_denied_host_never_reaches_a_socket(self):
        policy._load.cache_clear()
        with self.assertRaises(client.SourceUnavailable) as ctx:
            client.fetch_json(adapter(), path='/search')
        self.assertEqual(str(ctx.exception), 'host-denied')


# --------------------------------------------------------------------------- #
# §8.1a — the deny policy
# --------------------------------------------------------------------------- #

class HostMatchingTests(TestCase):
    """A denied host is denied with its subdomains, and after normalisation —
    `evil.example` that does not also refuse `api.evil.example` refuses nothing,
    because one DNS record is not a barrier."""

    def test_an_exact_host_matches(self):
        self.assertTrue(host_matches('evil.example', 'evil.example'))

    def test_every_label_below_it_matches(self):
        self.assertTrue(host_matches('api.v2.evil.example', 'evil.example'))

    def test_a_lookalike_suffix_does_not_match(self):
        self.assertFalse(host_matches('notevil.example', 'evil.example'))

    def test_case_and_trailing_dots_are_normalised(self):
        self.assertTrue(host_matches('API.Evil.Example.', 'evil.example'))

    def test_an_idn_homograph_is_matched_on_its_a_label(self):
        self.assertTrue(host_matches('exämple.com', 'xn--exmple-cua.com'))
        self.assertTrue(host_matches('xn--exmple-cua.com', 'exämple.com'))

    def test_a_cidr_entry_matches_an_address(self):
        self.assertTrue(host_matches('203.0.113.9', '203.0.113.0/24'))
        self.assertFalse(host_matches('203.0.114.9', '203.0.113.0/24'))

    def test_an_unparseable_entry_matches_nothing_rather_than_everything(self):
        """A typo in a denylist must fail open on that line and leave the rest of
        the list working — the alternative is one bad character switching every
        source off with nothing saying why."""
        self.assertFalse(host_matches('example.com', '///'))


class HostPolicyTests(TestCase):
    def setUp(self):
        policy._load.cache_clear()
        cache.clear()

    @override_settings(DATASOURCE_HOST_POLICY='', DATASOURCE_DENIED_HOSTS='')
    def test_the_default_is_open(self):
        """D14 — default-open, hosts refused as they prove to be a problem.
        Reading that as "no checks" would be exactly backwards: the address
        checks decide where the packet goes, this decides who we refuse to talk
        to on purpose."""
        self.assertTrue(policy.host_allowed('api.themoviedb.org'))

    @override_settings(DATASOURCE_HOST_POLICY='',
                       DATASOURCE_DENIED_HOSTS='evil.example, bad.test')
    def test_the_static_fallback_denies(self):
        self.assertFalse(policy.host_allowed('api.evil.example'))
        self.assertTrue(policy.host_allowed('good.test'))

    @override_settings(DATASOURCE_HOST_POLICY='no.such.module.host_allowed')
    def test_an_unimportable_policy_closes_rather_than_opens(self):
        """A typo in a setting must not silently switch a deny policy off."""
        self.assertFalse(policy.host_allowed('api.themoviedb.org'))

    def test_an_empty_host_is_never_allowed(self):
        self.assertFalse(policy.host_allowed(''))


# --------------------------------------------------------------------------- #
# §6 — the mapper
# --------------------------------------------------------------------------- #

class ResolveSlotsTests(TestCase):
    """The adapter's half, tested against a recorded provider payload with no
    application in sight — which is exactly what splitting the two hops buys."""

    TMDB = {'results': [
        {'id': 438631, 'title': 'Dune', 'release_date': '2021-09-15',
         'overview': 'Paul Atreides…', 'vote_average': 7.8,
         'credits': {'cast': [{'name': 'Timothée Chalamet'}, {'name': 'Zendaya'}]}},
        {'id': 41400, 'title': 'Dune', 'release_date': '1984-12-14'},
    ]}

    def test_the_result_path_is_walked(self):
        candidates = mapping.resolve_slots(self.TMDB, adapter(
            provides={'title': 'title', 'synopsis': 'overview'}))
        self.assertEqual(len(candidates), 2)
        self.assertEqual(candidates[0]['label'], 'Dune')
        self.assertEqual(candidates[0]['id'], '438631')

    def test_a_blank_result_path_means_the_payload_is_the_list(self):
        candidates = mapping.resolve_slots(
            self.TMDB['results'], adapter(result_path=''))
        self.assertEqual(len(candidates), 2)

    def test_an_absent_path_is_absent_never_an_empty_string(self):
        """A missing synopsis must leave the field untouched so the required-field
        check still fires, rather than filling it with "" and satisfying the check
        with nothing."""
        candidates = mapping.resolve_slots(self.TMDB, adapter(
            provides={'title': 'title', 'synopsis': 'overview'}))
        self.assertIn('synopsis', candidates[0]['slots'])
        self.assertNotIn('synopsis', candidates[1]['slots'])

    def test_a_list_hop_is_joined(self):
        candidates = mapping.resolve_slots(self.TMDB, adapter(
            provides={'cast': 'credits.cast[].name'}))
        self.assertEqual(candidates[0]['slots']['cast'], 'Timothée Chalamet, Zendaya')

    def test_a_slot_landing_on_a_container_is_dropped(self):
        candidates = mapping.resolve_slots(self.TMDB, adapter(
            provides={'credits': 'credits'}))
        self.assertEqual(candidates[0]['slots'], {})

    def test_a_missing_result_path_yields_no_candidates_rather_than_raising(self):
        self.assertEqual(mapping.resolve_slots({'nope': 1}, adapter()), [])

    def test_the_first_page_is_capped(self):
        payload = {'results': [{'id': i, 'title': f't{i}'} for i in range(200)]}
        self.assertEqual(len(mapping.resolve_slots(payload, adapter())),
                         mapping.MAX_CANDIDATES)


class BindValuesTests(TestCase):
    """The binding's half, tested with no network in sight."""

    def _binding(self, **over):
        data = dict(entity='Film', adapter_slug='tmdb',
                    field_map={'titre': 'title', 'annee': 'year', 'note': 'rating'},
                    field_types={'titre': 'string', 'annee': 'integer', 'note': 'decimal'})
        data.update(over)
        return BindingSpec(**data)

    def test_slots_become_this_applications_field_names(self):
        values = mapping.bind_values({'title': 'Dune'}, self._binding())
        self.assertEqual(values, {'titre': 'Dune'})

    def test_a_decimal_field_receives_a_number_never_the_string_the_api_sent(self):
        """§6 — or the platform re-acquires prod app 6's bug through a new door,
        where `1 * "175.5"` is string repetition and the aggregate answers
        "unknown" forever."""
        values = mapping.bind_values({'rating': '7.8'}, self._binding())
        self.assertEqual(values['note'], 7.8)
        self.assertNotIsInstance(values['note'], str)

    def test_a_string_field_keeps_a_reference_code_as_text(self):
        """A `string` field holding "007" is text — coercion is by the DECLARED
        type, never by what the value looks like."""
        values = mapping.bind_values(
            {'title': '007'},
            self._binding(field_map={'titre': 'title'}, field_types={'titre': 'string'}))
        self.assertEqual(values['titre'], '007')

    def test_an_iso_date_fills_an_integer_year_field(self):
        values = mapping.bind_values({'year': '2021-09-15'}, self._binding())
        self.assertEqual(values['annee'], 2021)

    def test_an_unmapped_slot_is_ignored(self):
        self.assertEqual(mapping.bind_values({'director': 'Villeneuve'}, self._binding()), {})

    def test_a_value_that_cannot_be_coerced_is_absent_rather_than_zero(self):
        values = mapping.bind_values({'rating': 'n/a'}, self._binding())
        self.assertNotIn('note', values)

    def test_an_ambiguous_date_is_refused_rather_than_guessed(self):
        values = mapping.bind_values(
            {'d': '03/04/2026'},
            BindingSpec(field_map={'when': 'd'}, field_types={'when': 'date'}))
        self.assertEqual(values, {})

    def test_an_iso_date_is_kept(self):
        values = mapping.bind_values(
            {'d': '2026-04-03'},
            BindingSpec(field_map={'when': 'd'}, field_types={'when': 'date'}))
        self.assertEqual(values, {'when': '2026-04-03'})

    def test_a_bare_year_fills_a_date_field_at_january(self):
        values = mapping.bind_values(
            {'d': '1984'},
            BindingSpec(field_map={'when': 'd'}, field_types={'when': 'date'}))
        self.assertEqual(values, {'when': '1984-01-01'})

    def test_a_boolean_reads_the_words_a_json_api_uses(self):
        binding = BindingSpec(field_map={'ok': 'flag'}, field_types={'ok': 'boolean'})
        self.assertIs(mapping.bind_values({'flag': 'true'}, binding)['ok'], True)
        self.assertIs(mapping.bind_values({'flag': False}, binding)['ok'], False)
        self.assertEqual(mapping.bind_values({'flag': 'maybe'}, binding), {})


# --------------------------------------------------------------------------- #
# §8.3 / §8.4 — the guards and the three honest failures
# --------------------------------------------------------------------------- #

class GuardTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_an_open_breaker_stops_the_call_before_the_meter_is_spent(self):
        breaker.trip(breaker.scope_key(7, 'stub'), 'refused:401')
        with self.assertRaises(services.LookupError_) as ctx:
            services.search(adapter(), BindingSpec(), 'dune', application_id=7)
        self.assertEqual(ctx.exception.key, services.UNAVAILABLE)
        self.assertEqual(throttle.daily_used(7), 0)

    @override_settings(DATASOURCE_DAILY_PER_APPLICATION=2)
    def test_an_exhausted_daily_ceiling_is_named_never_an_empty_list(self):
        """The `route-not-found`-vs-`routing-engine-unavailable` mistake in a new
        module: an empty candidate list that actually means *you have run out*."""
        self.assertTrue(throttle.consume_daily(9))
        self.assertTrue(throttle.consume_daily(9))
        with self.assertRaises(services.LookupError_) as ctx:
            services.search(adapter(), BindingSpec(), 'dune', application_id=9)
        self.assertEqual(ctx.exception.key, services.QUOTA_EXHAUSTED)

    @override_settings(DATASOURCE_DAILY_PER_APPLICATION=0)
    def test_a_zero_daily_ceiling_means_no_ceiling(self):
        self.assertTrue(throttle.consume_daily(11))

    @override_settings(DATASOURCE_RATE_PER_MINUTE=0)
    def test_the_per_caller_throttle_is_off_by_default(self):
        request = mock.Mock(META={'REMOTE_ADDR': '1.2.3.4'})
        self.assertTrue(all(throttle.allow(request) for _ in range(50)))

    @override_settings(DATASOURCE_RATE_PER_MINUTE=3)
    def test_the_per_caller_throttle_bounds_a_loop(self):
        request = mock.Mock(META={'REMOTE_ADDR': '1.2.3.4'})
        self.assertEqual(sum(1 for _ in range(10) if throttle.allow(request)), 3)

    def test_a_401_trips_the_breaker_so_a_dead_key_stops_costing(self):
        with mock.patch.object(client, 'fetch_json',
                               side_effect=client.SourceRefused('refused', status=401)):
            with self.assertRaises(services.LookupError_) as ctx:
                services.search(adapter(), BindingSpec(), 'x', application_id=3)
        self.assertEqual(ctx.exception.key, services.REFUSED)
        self.assertEqual(ctx.exception.status, 401)
        self.assertTrue(breaker.is_tripped(breaker.scope_key(3, 'stub')))

    def test_a_lost_packet_does_not_take_a_source_away(self):
        with mock.patch.object(client, 'fetch_json',
                               side_effect=client.SourceUnavailable('transport:Timeout')):
            with self.assertRaises(services.LookupError_):
                services.search(adapter(), BindingSpec(), 'x', application_id=4)
        self.assertFalse(breaker.is_tripped(breaker.scope_key(4, 'stub')))

    def test_a_refusal_of_ours_is_remembered(self):
        with mock.patch.object(client, 'fetch_json',
                               side_effect=client.SourceUnavailable('host-denied')):
            with self.assertRaises(services.LookupError_):
                services.search(adapter(), BindingSpec(), 'x', application_id=5)
        self.assertTrue(breaker.is_tripped(breaker.scope_key(5, 'stub')))

    def test_the_breaker_reason_is_stored_and_never_published(self):
        breaker.trip('k', 'quota exceeded for key sk-ABC123')
        self.assertIn('ABC123', breaker.reason('k'))
        with self.assertRaises(services.LookupError_) as ctx:
            services.search(adapter(), BindingSpec(), 'x', application_id=0)
        self.assertNotIn('ABC123', str(ctx.exception))


class SearchAndDetailTests(TestCase):
    def setUp(self):
        cache.clear()

    def _binding(self):
        return BindingSpec(entity='Film', adapter_slug='stub',
                           field_map={'titre': 'title', 'annee': 'year'},
                           field_types={'titre': 'string', 'annee': 'integer'})

    def test_a_search_answers_this_applications_field_names(self):
        payload = {'results': [{'id': 1, 'title': 'Dune', 'year': '2021'}]}
        with mock.patch.object(client, 'fetch_json', return_value=payload):
            candidates = services.search(adapter(), self._binding(), 'dune',
                                         application_id=1)
        self.assertEqual(candidates, [{'label': 'Dune', 'id': '1',
                                       'values': {'titre': 'Dune', 'annee': 2021}}])

    def test_nothing_is_written_by_a_lookup(self):
        """*An external source fills a form; it never writes a row.* Asserted by
        reading the module rather than by trusting the sentence: a source that
        could write a row would be a second write path past the required check,
        the role gate, the computed fields, the normalisation and row
        visibility."""
        import inspect
        source = inspect.getsource(services)
        for forbidden in ('.objects.create', '.save(', 'SandboxRecord'):
            self.assertNotIn(forbidden, source)

    def test_the_two_step_flow_fires_a_second_request_on_the_pick(self):
        detail_payload = {'id': 1, 'title': 'Dune', 'year': '2021',
                          'overview': 'Paul Atreides…'}
        spec = adapter(detail_path='/movie/{id}',
                       provides={'title': 'title', 'year': 'year', 'synopsis': 'overview'})
        binding = BindingSpec(field_map={'resume': 'synopsis'},
                              field_types={'resume': 'text'})
        with mock.patch.object(client, 'fetch_json', return_value=detail_payload) as call:
            picked = services.detail(spec, binding, 1, application_id=1)
        self.assertEqual(call.call_args.kwargs['path'], '/movie/1')
        self.assertEqual(picked['values'], {'resume': 'Paul Atreides…'})

    def test_a_detail_call_on_a_one_step_adapter_is_refused(self):
        with self.assertRaises(services.LookupError_):
            services.detail(adapter(), self._binding(), 1, application_id=1)


class ProbeTests(TestCase):
    """§5.4 item 3 — one real search. `result_path` must resolve to a list and at
    least one declared slot must resolve inside its first element, because an
    adapter that fails either looks like an API with no data forever."""

    def setUp(self):
        cache.clear()

    def test_a_working_declaration_passes_and_shows_what_it_read(self):
        payload = {'results': [{'id': 1, 'title': 'Dune', 'year': '2021'}]}
        with mock.patch.object(client, 'fetch_json', return_value=payload):
            ok, detail = services.probe(adapter(), application_id=1)
        self.assertTrue(ok)
        self.assertEqual(detail['slots'], {'title': 'Dune', 'year': '2021'})

    def test_a_result_path_that_resolves_to_nothing_fails(self):
        with mock.patch.object(client, 'fetch_json', return_value={'items': []}):
            ok, detail = services.probe(adapter(), application_id=1)
        self.assertFalse(ok)
        self.assertEqual(detail['code'], 'probe_no_results')

    def test_a_declaration_whose_slots_resolve_to_nothing_fails(self):
        with mock.patch.object(client, 'fetch_json',
                               return_value={'results': [{'nope': 1}]}):
            ok, detail = services.probe(adapter(), application_id=1)
        self.assertFalse(ok)
        self.assertEqual(detail['code'], 'probe_no_slot_resolved')

    def test_a_refusal_is_reported_as_itself(self):
        with mock.patch.object(client, 'fetch_json',
                               side_effect=client.SourceRefused('x', status=401)):
            ok, detail = services.probe(adapter(), application_id=1)
        self.assertFalse(ok)
        self.assertEqual(detail['code'], services.REFUSED)
        self.assertEqual(detail['status'], 401)


class FreeEverywhereTests(TestCase):
    """D6 — free, everywhere. No AI provider is reached by a lookup, an adoption
    or a probe, so the module goes nowhere near `ai_debit_credits` and nowhere
    near `credits.services`. `routing/tests.py` already has one of these, and
    this is deliberately the same test one module over.
    """

    FORBIDDEN = {'debit_credits', 'has_credits', 'ai_debit_credits',
                 'ai_has_credits', 'log_ai_call', 'get_client', 'create_completion'}

    def test_no_module_here_bills_anything_and_none_imports_generator(self):
        """Walked as an AST rather than grepped, in the manner of
        `test_ai_call_model_provenance`: prose in a docstring explaining that a
        lookup does not bill is not a billing call, and a test that cannot tell
        the difference gets deleted the first time it cries wolf.

        The same walk carries §10 item 2 — `datasource` is base-syncable and
        installable alone, so it must never import `generator` or `credits`.
        """
        import ast
        import inspect

        from . import access, addresses as addr, apps, hosts
        for module in (services, client, mapping, breaker, throttle, policy,
                       access, addr, hosts, apps):
            tree = ast.parse(inspect.getsource(module))
            called, imported = set(), set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    name = (func.attr if isinstance(func, ast.Attribute)
                            else getattr(func, 'id', None))
                    if name:
                        called.add(name)
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    module_name = getattr(node, 'module', '') or ''
                    self.assertNotIn('credits', module_name.split('.'),
                                     f'{module.__name__} must not import credits')
                    self.assertNotIn('generator', module_name.split('.'),
                                     f'{module.__name__} must not import generator')
                    imported.update(alias.name.split('.')[0] for alias in node.names)
            self.assertEqual(called & self.FORBIDDEN, set(),
                             f'{module.__name__} must not call a billing/AI helper')
            self.assertEqual(imported & self.FORBIDDEN, set(),
                             f'{module.__name__} must not import a billing/AI helper')


class WritePathTests(TestCase):
    """§10 item 4 — the write path stays single.

    *An external source fills a form; it never writes a row.* A lookup returns
    values and the existing create endpoint writes them, so the required check,
    the role gate, the computed fields, the geo and numeric normalisation and row
    visibility all keep running with nothing re-implemented.
    """

    def test_nothing_in_the_module_writes_a_row(self):
        import ast
        import inspect

        for module in (services, client, mapping):
            tree = ast.parse(inspect.getsource(module))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    self.assertNotIn(node.func.attr, ('create', 'bulk_create', 'update'),
                                     f'{module.__name__} looks like it writes')
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    names = [a.name for a in node.names]
                    self.assertNotIn('SandboxRecord', names)
