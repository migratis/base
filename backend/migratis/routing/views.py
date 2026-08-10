"""Routing API — snap waypoints to roads, and say honestly when you cannot.

Two endpoints, no models, no billing. Snapping is deterministic and reaches no
AI provider, so it goes nowhere near ``ai_debit_credits`` and nowhere near
``credits.services``: it is free, like every other deterministic path
(SCOPE_road_routing.md §8.3), and a test reads this module's source to keep it
that way.

**Both endpoints are ``auth=None``.** The sandbox is public by design, and a
generated app may let an anonymous role create records — a login-gated snap
would mean the map editor works for the owner and silently draws straight lines
for everyone else, which is precisely the failure this scope exists to remove.
The exposure is bounded rather than authenticated: the engine URL comes from
settings and never from the request (no SSRF), the input is capped at
``MAX_WAYPOINTS`` and range-checked before any network call, nothing is written,
and nothing is charged. Same posture as the public crash-telemetry endpoints.
"""
from django.http import JsonResponse
from ninja import Router

from . import engines, services
from .schemas import SnapIn

router = Router()


def _detail(key, message):
    return [{'loc': ['routing'], 'msg': key, 'type': message}]


@router.post('/snap', auth=None)
def snap(request, payload: SnapIn):
    """Waypoints + profile → road-following geometry (§4 shape).

    Every failure is *named*. The caller keeps whatever line the user traced and
    badges it with the reason; it never discards the edit and never presents a
    straight line as if it followed roads.
    """
    try:
        geometry = services.snap_route(payload.waypoints, payload.profile)
    except services.InvalidWaypoints as exc:
        return JsonResponse({'detail': _detail(str(exc), 'invalid-waypoints')}, status=422)
    except engines.UnsupportedProfile:
        return JsonResponse({'detail': _detail('route-profile-unsupported',
                                               'unsupported-profile')}, status=422)
    except engines.RouteNotFound as exc:
        # §5 row 3 — the engine's own reason is the useful part here ("no
        # suitable edges near location" tells the user to move a waypoint).
        # Route-level text only: a transport failure never reaches this branch,
        # so no hostname or internal address can ride out on it.
        return JsonResponse({'detail': _detail('route-not-found', 'no-route'),
                             'engine_reason': str(exc)[:200]}, status=422)
    except engines.EngineUnavailable as exc:
        # Told apart so the UI can hide the affordance in one case and badge it
        # in the other. The engine's text is deliberately dropped.
        key = ('routing-engine-not-configured' if str(exc) == 'not-configured'
               else 'routing-engine-unavailable')
        return JsonResponse({'detail': _detail(key, 'engine-unavailable')}, status=503)

    return JsonResponse(geometry)


@router.get('/availability', auth=None)
def availability(request):
    """Whether waypoint mode should be offered at all, measured now.

    Read once by the map editor. ``not_configured`` means the feature was never
    asked for on this host, so nothing is shown and no error is raised;
    ``unavailable`` means it was asked for and is down, which the user must see.
    Never publishes the engine's error — same rule as the AI breaker reason.
    """
    state, engine_name = services.engine_state()
    return JsonResponse({
        'available': state == 'operational',
        'state':     state,
        'engine':    engine_name,
        'profiles':  list(services.ROUTE_PROFILES),
    })
