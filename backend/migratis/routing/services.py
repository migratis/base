"""Turning waypoints into a storable geometry.

The storage shape is the whole design decision here (SCOPE_road_routing.md §4).
Storing only the snapped 800-point LineString would make the route
*uneditable* — nobody can drag waypoint 3 when all that survives is 800
anonymous vertices. So both are stored, and the waypoints ride as a **foreign
member** on the geometry:

    {"type": "LineString", "coordinates": [...800...],
     "routing": {"waypoints": [...3...], "profile": "bicycle",
                 "engine": "valhalla", "distance_m": 41230,
                 "snapped_at": "..."}}

GeoJSON permits foreign members, and every existing reader (MapView, MapDisplay,
GeoValue, geoSummary, and their four codegen copies) accepts a value on the
strength of `type` + `Array.isArray(coordinates)` and ignores the rest — so not
one of them changes. Wrapping the value in a GeoJSON `Feature` would be more
orthodox and would break all of them plus every geometry already stored in
production.

A route with no `routing` member is a hand-traced line: exactly what exists
today, still valid, still readable.
"""
from datetime import datetime, timezone

from . import engines
from .engines import ROUTE_PROFILES  # re-exported: the callers' single source

DEFAULT_PROFILE = 'bicycle'

# A route the user traced by hand. Well above any realistic itinerary and low
# enough that an unauthenticated caller cannot turn the endpoint into a load
# generator against the engine.
MAX_WAYPOINTS = 100


class InvalidWaypoints(ValueError):
    """The request is not a route: too few points, too many, or off-planet."""


def validate_waypoints(waypoints):
    """Return the waypoints as ``[[lng, lat], ...]`` floats, or raise.

    Validated before the engine is touched, so a malformed request costs one
    Python function call and no network round trip.
    """
    if not isinstance(waypoints, (list, tuple)) or len(waypoints) < 2:
        raise InvalidWaypoints('route-needs-two-waypoints')
    if len(waypoints) > MAX_WAYPOINTS:
        raise InvalidWaypoints('route-too-many-waypoints')

    cleaned = []
    for point in waypoints:
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            raise InvalidWaypoints('route-invalid-waypoint')
        try:
            lng, lat = float(point[0]), float(point[1])
        except (TypeError, ValueError):
            raise InvalidWaypoints('route-invalid-waypoint')
        # GeoJSON order is [lng, lat]; a flipped pair is the classic bug and
        # latitudes above 90 are the only symptom that ever surfaces.
        if not (-180.0 <= lng <= 180.0) or not (-90.0 <= lat <= 90.0):
            raise InvalidWaypoints('route-invalid-waypoint')
        cleaned.append([lng, lat])
    return cleaned


def snap_route(waypoints, profile=DEFAULT_PROFILE):
    """Snap `waypoints` to the road network and return the §4 geometry.

    Raises ``engines.EngineUnavailable`` when there is no engine to ask,
    ``engines.RouteNotFound`` when the engine says there is no route, and
    ``InvalidWaypoints`` when the request was never a route.
    """
    points = validate_waypoints(waypoints)
    if profile not in ROUTE_PROFILES:
        raise engines.UnsupportedProfile(profile)

    engine = engines.get_engine()
    if engine is None:
        raise engines.EngineUnavailable('not-configured')

    result = engine.route(points, profile)
    return {
        'type': 'LineString',
        'coordinates': result.coordinates,
        'routing': {
            'waypoints': points,
            'profile': result.profile or profile,
            'engine': result.engine,
            'distance_m': result.distance_m,
            'snapped_at': datetime.now(timezone.utc).isoformat(),
        },
    }


def engine_state():
    """``(state, engine_name)`` for /status and the availability probe.

    ``not_configured`` and ``unavailable`` are different answers on purpose:
    the first hides the waypoint affordance entirely (the feature was never
    asked for), the second shows it with a badge naming why the line is
    straight. Never carries the engine's own error text.
    """
    engine = engines.get_engine()
    if engine is None:
        return 'not_configured', None
    return ('operational' if engine.probe() else 'unavailable'), engine.name
