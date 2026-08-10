"""Routing engine adapters.

The tiles on screen are images; they carry no road graph, so road-following
geometry has to be computed by an engine that has ingested the OSM road network
(SCOPE_road_routing.md §1). This module is the whole of Migratis' knowledge of
that engine — one small interface, one implementation.

**Valhalla** is the implementation (owner decision D1). The deciding factor was
not speed: Valhalla serves many costings against **one** tile set, chosen per
request, so bicycle and auto need one container and one preprocessing run. OSRM
prepares one dataset per profile, and the second one always gets forgotten.

Three failure modes are told apart on purpose, because the caller does different
things with each (§5):

* ``EngineUnavailable`` — no engine configured, unreachable, or 5xx. The traced
  line is kept and badged. Never a silent straight line.
* ``RouteNotFound``     — the engine answered and there is no route (an island,
  a pedestrian-only waypoint). Its own reason is worth surfacing.
* ``UnsupportedProfile``— a caller asked for a costing we do not offer. Refused
  before any network call.
"""
from dataclasses import dataclass, field as dc_field

import requests
from django.conf import settings


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


ENGINES = {
    'valhalla': ValhallaEngine,
}


def get_engine():
    """The configured engine, or None when routing is not set up.

    None is a first-class answer, not an error: a host that runs no engine is
    the expected case for an installed app (§10), and every caller degrades on
    it by name.
    """
    url = getattr(settings, 'ROUTING_ENGINE_URL', '') or ''
    if not url:
        return None
    engine_cls = ENGINES.get(getattr(settings, 'ROUTING_ENGINE', 'valhalla') or 'valhalla')
    if engine_cls is None:
        # An operator typed a dialect we do not implement. Answering "no engine"
        # is honest; guessing a dialect against a real host is not.
        return None
    timeout = getattr(settings, 'ROUTING_ENGINE_TIMEOUT', DEFAULT_TIMEOUT)
    return engine_cls(url, timeout=timeout)
