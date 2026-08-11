"""Routing engine adapters.

The tiles on screen are images; they carry no road graph, so road-following
geometry has to be computed by an engine that has ingested the OSM road network
(SCOPE_road_routing.md@8914275 §1). This module is the whole of Migratis'
knowledge of that engine — one small interface, now two implementations, and
that number is the design rather than a stage on the way somewhere.

**Two worlds** (SCOPE_routing_sandbox_external.md@c170e1a D3′): *the sandbox routes
worldwide against someone else's engine; a generated app routes inside one
extract against an engine its owner built; neither ever calls the other.*

* **ValhallaEngine** is what an installed app runs (owner decision D1). The
  deciding factor was not speed: Valhalla serves many costings against **one**
  tile set, chosen per request, so bicycle and auto need one container and one
  preprocessing run. OSRM prepares one dataset per profile, and the second one
  always gets forgotten.
* **ORSEngine** is what migratis.ai's design sandbox uses, so that a designer
  can try a `route` field before deciding to ship it — the choice of
  `Field.route_profile` is made at design time, and a designer who cannot try it
  picks blind. Building a country-scale tile set on the box that also runs dev,
  production and one postgres is what made the alternative unattractive.

This module is one file in both repos and **which world you are in is a
setting**, never a fork: an installed app defaults to `valhalla` with no API
key, so the ORS adapter is present and unreachable there — it cannot call
anything without a key its owner chose to supply. That is what keeps §4's
promise literally true: no end user of a generated app has coordinates sent to
anyone, including us.

Whichever answered, the **stored shape is identical** (§5.1). ``RouteResult`` is
the normalisation boundary and everything engine-specific stops at it: six
readers consume the stored value on the strength of `type` +
`Array.isArray(coordinates)`, and two engine-specific contracts would be exactly
the sandbox↔codegen divergence this project has already retired one roadmap over.

Three failure modes are told apart on purpose, because the caller does different
things with each (§5):

* ``EngineUnavailable`` — no engine configured, unreachable, or 5xx. The traced
  line is kept and badged. Never a silent straight line.
* ``RouteNotFound``     — the engine answered and there is no route (an island,
  a pedestrian-only waypoint). Its own reason is worth surfacing.
* ``UnsupportedProfile``— a caller asked for a costing we do not offer. Refused
  before any network call.
"""
import time
from dataclasses import dataclass, field as dc_field

import requests
from django.conf import settings
from django.core.cache import cache

from . import breaker


# Profiles Migratis offers, in the order they should be listed to a designer.
# `Field.route_profile` in the generator mirrors this list — a parity test in
# migratis.generator keeps the two from drifting.
ROUTE_PROFILES = ('bicycle', 'auto', 'pedestrian')

DEFAULT_TIMEOUT = 20        # seconds — a country-scale route is fast; a hang is not
PROBE_TIMEOUT   = 3         # the reachability probe must never delay a page


class RoutingError(Exception):
    """Base for every routing failure."""


class EngineUnavailable(RoutingError):
    """No engine configured, unreachable, or answering 5xx.

    Deliberately carries no engine text: this is the case whose message quotes
    hostnames and internal addresses, and it is published on /status.
    """


class RouteNotFound(RoutingError):
    """The engine answered and could not route between these waypoints."""


class UnsupportedProfile(RoutingError):
    """A costing Migratis does not offer."""


@dataclass
class RouteResult:
    coordinates: list          # GeoJSON [lng, lat] pairs, snapped to the road graph
    distance_m: int            # the engine's own number, not a great-circle guess
    profile: str = ''
    engine: str = ''
    meta: dict = dc_field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Encoded polyline (Google algorithm, arbitrary precision)
# --------------------------------------------------------------------------- #
# Valhalla returns geometry as an encoded polyline at precision 6, never as
# GeoJSON, so a decoder is not optional. Both directions are implemented because
# the round-trip is what the tests pin — decoding at the wrong precision does not
# raise, it silently returns coordinates 10× off.

def decode_polyline(encoded, precision=6):
    """Decode an encoded polyline into GeoJSON-order ``[lng, lat]`` pairs."""
    if not encoded:
        return []
    factor = float(10 ** precision)
    coords, index, lat, lng = [], 0, 0, 0
    length = len(encoded)
    while index < length:
        for is_lat in (True, False):
            result, shift = 0, 0
            while True:
                if index >= length:
                    return coords
                byte = ord(encoded[index]) - 63
                index += 1
                result |= (byte & 0x1F) << shift
                shift += 5
                if byte < 0x20:
                    break
            delta = ~(result >> 1) if result & 1 else (result >> 1)
            if is_lat:
                lat += delta
            else:
                lng += delta
        coords.append([round(lng / factor, 6), round(lat / factor, 6)])
    return coords


def _encode_value(value, out):
    value = ~(value << 1) if value < 0 else (value << 1)
    while value >= 0x20:
        out.append(chr((0x20 | (value & 0x1F)) + 63))
        value >>= 5
    out.append(chr(value + 63))


def encode_polyline(coordinates, precision=6):
    """Encode GeoJSON-order ``[lng, lat]`` pairs into an encoded polyline."""
    factor = 10 ** precision
    out, prev_lat, prev_lng = [], 0, 0
    for lng, lat in coordinates or []:
        ilat, ilng = int(round(lat * factor)), int(round(lng * factor))
        _encode_value(ilat - prev_lat, out)
        _encode_value(ilng - prev_lng, out)
        prev_lat, prev_lng = ilat, ilng
    return ''.join(out)


# --------------------------------------------------------------------------- #
# Valhalla
# --------------------------------------------------------------------------- #
class ValhallaEngine:
    """Adapter for a self-hosted Valhalla (`ghcr.io/valhalla/valhalla`).

    Speaks only to ``settings.ROUTING_ENGINE_URL`` — the URL is never taken from
    a request, so no caller can point this at a host of their choosing.
    """

    name = 'valhalla'

    # Migratis profile → Valhalla costing. The identity mapping today; kept
    # explicit so a profile we offer can never be passed through unvalidated.
    COSTINGS = {
        'bicycle':    'bicycle',
        'auto':       'auto',
        'pedestrian': 'pedestrian',
    }

    def __init__(self, base_url, timeout=DEFAULT_TIMEOUT):
        self.base_url = (base_url or '').rstrip('/')
        self.timeout = timeout

    # -- public ------------------------------------------------------------ #
    def route(self, waypoints, profile):
        costing = self.COSTINGS.get(profile)
        if not costing:
            raise UnsupportedProfile(profile)

        payload = {
            'locations': [{'lat': lat, 'lon': lng} for lng, lat in waypoints],
            'costing': costing,
            'directions_options': {'units': 'kilometers'},
        }
        try:
            response = requests.post(f'{self.base_url}/route', json=payload,
                                     timeout=self.timeout)
        except requests.exceptions.RequestException as exc:
            raise EngineUnavailable(str(exc)) from exc

        if response.status_code >= 500:
            # The engine is there but broken — same caller behaviour as absent.
            raise EngineUnavailable(f'engine returned {response.status_code}')
        if response.status_code >= 400:
            raise RouteNotFound(self._error_text(response))

        try:
            trip = (response.json() or {}).get('trip') or {}
        except ValueError as exc:
            raise EngineUnavailable('engine returned a non-JSON body') from exc

        coordinates = self._shape(trip)
        if len(coordinates) < 2:
            # A trip with no drawable shape is a failed route, not an empty line:
            # storing [] would render as nothing with no explanation anywhere.
            raise RouteNotFound('engine returned no geometry')

        summary = trip.get('summary') or {}
        return RouteResult(
            coordinates=coordinates,
            distance_m=int(round(float(summary.get('length') or 0) * 1000)),
            profile=profile,
            engine=self.name,
            meta={'duration_s': int(round(float(summary.get('time') or 0)))},
        )

    def probe(self):
        """True when the engine answers. Never raises and never returns the
        reason — the reason quotes internal hostnames and this feeds /status."""
        try:
            response = requests.get(f'{self.base_url}/status', timeout=PROBE_TIMEOUT)
        except requests.exceptions.RequestException:
            return False
        return response.status_code < 500

    # -- internals --------------------------------------------------------- #
    @staticmethod
    def _error_text(response):
        try:
            body = response.json() or {}
        except ValueError:
            return (response.text or '')[:200]
        return str(body.get('error') or body.get('error_code') or 'no route')[:200]

    @staticmethod
    def _shape(trip):
        """Concatenate the legs' shapes, dropping each joint's duplicate vertex.

        Valhalla ends leg N and starts leg N+1 on the same point; keeping both
        leaves a zero-length segment at every waypoint, which Geoman then offers
        as two draggable vertices sitting on top of each other.
        """
        coordinates = []
        for leg in trip.get('legs') or []:
            leg_coords = decode_polyline(leg.get('shape') or '', precision=6)
            if coordinates and leg_coords:
                leg_coords = leg_coords[1:]
            coordinates.extend(leg_coords)
        return coordinates


# --------------------------------------------------------------------------- #
# openrouteservice
# --------------------------------------------------------------------------- #
class ORSEngine:
    """Adapter for openrouteservice (HeiGIT / Heidelberg — EU-hosted).

    The engine migratis.ai itself uses (SCOPE_routing_sandbox_external.md@c170e1a D3′):
    **the sandbox routes worldwide against someone else's engine, a generated
    app routes inside one extract against an engine its owner built, and neither
    ever calls the other.**

    An installed app never reaches this class unless its owner deliberately
    selects it: `ROUTING_ENGINE` defaults to `valhalla` there and this adapter
    refuses to exist without an API key (see ``get_engine``). That is what keeps
    end users' coordinates out of everyone's hands including ours (§4) without
    the two repos having to carry different code.

    Three things separate it from ``ValhallaEngine``, and all three are confined
    to this class because the *stored* shape must stay engine-independent (§5.1):

    * It is **metered**. A quota stop is ``EngineUnavailable``, never
      ``RouteNotFound`` — telling a user their route is impossible because
      Migratis ran out of requests sends them to move a waypoint that was never
      the problem (§5.4). Every such stop trips the local ``breaker`` so the
      rejections stop becoming outbound calls.
    * It answers **GeoJSON**. ORS encodes polylines at precision 5 where
      Valhalla uses 6, and ``decode_polyline`` does not raise on the wrong one —
      it silently returns coordinates 10× off. Asking for ``/geojson`` deletes
      the whole class of bug rather than defending against it (§5.3).
    * Its costings are **its own vocabulary**. ``cycling-regular`` /
      ``driving-car`` / ``foot-walking`` never surface: ``ROUTE_PROFILES`` is
      the design-time vocabulary stored on ``Field.route_profile``, published in
      the agent guide, and ``COSTINGS`` is the only seam between them (§5.2).
    """

    name = 'ors'

    # A hosted service's address is a constant, not something an operator should
    # have to look up. `ROUTING_ENGINE_URL` still overrides it — for a
    # self-hosted ORS, or a staging host.
    DEFAULT_BASE_URL = 'https://api.openrouteservice.org'
    NEEDS_API_KEY = True

    COSTINGS = {
        'bicycle':    'cycling-regular',
        'auto':       'driving-car',
        'pedestrian': 'foot-walking',
    }

    # Statuses that mean "not now, and not because of your waypoints": a spent
    # quota (429), a key that is refused or out of allowance (403), a key that is
    # wrong (401). None of them is fixed by retrying, and all of them would
    # otherwise be reported as a route failure.
    CAPACITY_STATUSES = (401, 403, 429)

    PROBE_CACHE_SECONDS = 30

    def __init__(self, base_url, timeout=DEFAULT_TIMEOUT, api_key=''):
        self.base_url = (base_url or '').rstrip('/')
        self.timeout = timeout
        self.api_key = api_key or ''

    # -- public ------------------------------------------------------------ #
    def route(self, waypoints, profile):
        costing = self.COSTINGS.get(profile)
        if not costing:
            raise UnsupportedProfile(profile)

        if breaker.is_tripped(self.name):
            # The point of the breaker: refused before the network, so a client
            # retrying in a loop costs the provider nothing and us nothing.
            raise EngineUnavailable('breaker-tripped')

        url = f'{self.base_url}/v2/directions/{costing}/geojson'
        try:
            response = requests.post(
                url,
                # ORS speaks GeoJSON [lng, lat] natively — nothing to flip, and
                # a "helpful" swap here routes between two different places.
                json={'coordinates': [list(point) for point in waypoints]},
                headers={'Authorization': self.api_key,
                         'Content-Type': 'application/json',
                         'Accept': 'application/geo+json'},
                timeout=self.timeout)
        except requests.exceptions.RequestException as exc:
            raise EngineUnavailable(str(exc)) from exc

        if response.status_code in self.CAPACITY_STATUSES:
            reason = self._error_text(response)
            breaker.trip(self.name, reason=reason, seconds=self._reset_hint(response))
            raise EngineUnavailable(f'{response.status_code}: {reason}')
        if response.status_code >= 500:
            raise EngineUnavailable(f'engine returned {response.status_code}')
        if response.status_code >= 400:
            raise RouteNotFound(self._error_text(response))

        try:
            body = response.json() or {}
        except ValueError as exc:
            raise EngineUnavailable('engine returned a non-JSON body') from exc

        feature = (body.get('features') or [{}])[0]
        coordinates = ((feature.get('geometry') or {}).get('coordinates')) or []
        if len(coordinates) < 2:
            # A route with no drawable shape is a failed route, not an empty
            # line: storing [] renders as nothing with no explanation anywhere.
            raise RouteNotFound('engine returned no geometry')

        summary = ((feature.get('properties') or {}).get('summary')) or {}
        return RouteResult(
            coordinates=[[c[0], c[1]] for c in coordinates],
            # ORS answers in metres already; Valhalla answers in kilometres.
            # Both store metres — a `formula_field` totalling a stage list adds
            # these numbers, so the unit cannot be ambiguous.
            distance_m=int(round(float(summary.get('distance') or 0))),
            profile=profile,
            engine=self.name,
            meta={'duration_s': int(round(float(summary.get('duration') or 0)))},
        )

    def probe(self):
        """True when the engine answers. Never raises and never returns why.

        Cached, unlike Valhalla's: ``/routing/availability`` is read once per
        page load *per visitor* and is not gated, so an uncached probe turns a
        busy sandbox into a stream of calls at someone else's host.
        """
        if breaker.is_tripped(self.name):
            return False
        cached = cache.get(_PROBE_CACHE_KEY)
        if cached is not None:
            return bool(cached)
        try:
            response = requests.get(f'{self.base_url}/v2/health',
                                    headers={'Authorization': self.api_key},
                                    timeout=PROBE_TIMEOUT)
            reachable = response.status_code < 500
        except requests.exceptions.RequestException:
            reachable = False
        cache.set(_PROBE_CACHE_KEY, 1 if reachable else 0, self.PROBE_CACHE_SECONDS)
        return reachable

    # -- internals --------------------------------------------------------- #
    @staticmethod
    def _error_text(response):
        """ORS words its errors two ways: ``{"error": {"code", "message"}}`` for
        a routing problem and a bare ``{"error": "Rate limit exceeded"}`` for a
        capacity one. Both are read, because the second is the one that decides
        whether a user is told to move a waypoint."""
        try:
            body = response.json() or {}
        except ValueError:
            return (response.text or '')[:200]
        error = body.get('error')
        if isinstance(error, dict):
            return str(error.get('message') or error.get('code') or 'no route')[:200]
        return str(error or body.get('message') or 'no route')[:200]

    @staticmethod
    def _reset_hint(response):
        """Seconds until the provider's window reopens, when it says so.

        Clamped by ``breaker.trip``: this is a number from someone else's host,
        and an absurd one would either flap or switch routing off for a week.
        """
        headers = getattr(response, 'headers', None) or {}
        raw = headers.get('X-Ratelimit-Reset') or headers.get('x-ratelimit-reset')
        if not raw:
            return None
        try:
            value = int(float(raw))
        except (TypeError, ValueError):
            return None
        if value > 10 ** 9:
            # An epoch timestamp rather than a duration — both shapes are in the
            # wild, and subtracting the wrong one gives a 55-year outage.
            value -= int(time.time())
        return value if value > 0 else None


_PROBE_CACHE_KEY = 'routing:probe:ors'


ENGINES = {
    'valhalla': ValhallaEngine,
    'ors':      ORSEngine,
}


def get_engine():
    """The configured engine, or None when routing is not set up.

    None is a first-class answer, not an error: a host that runs no engine is
    the expected case for an installed app (§10), and every caller degrades on
    it by name — waypoint mode is hidden entirely rather than offered and
    failing on every click.

    "Configured" is the engine's own question, which is why it is asked through
    the class. A self-hosted engine needs an address and nothing else; a hosted
    one knows its address and needs a key, and a keyless ORS is *not configured*
    rather than broken — every call would be refused, and an affordance that
    fails on every click is worse than one that was never offered.
    """
    engine_cls = ENGINES.get(getattr(settings, 'ROUTING_ENGINE', 'valhalla') or 'valhalla')
    if engine_cls is None:
        # An operator typed a dialect we do not implement. Answering "no engine"
        # is honest; guessing a dialect against a real host is not.
        return None

    url = (getattr(settings, 'ROUTING_ENGINE_URL', '') or '').strip()
    url = url or getattr(engine_cls, 'DEFAULT_BASE_URL', '')
    if not url:
        return None

    kwargs = {'timeout': getattr(settings, 'ROUTING_ENGINE_TIMEOUT', DEFAULT_TIMEOUT)}
    if getattr(engine_cls, 'NEEDS_API_KEY', False):
        api_key = (getattr(settings, 'ROUTING_ENGINE_KEY', '') or '').strip()
        if not api_key:
            return None
        kwargs['api_key'] = api_key
    return engine_cls(url, **kwargs)
