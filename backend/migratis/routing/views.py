"""Routing API — snap waypoints to roads, and say honestly when you cannot.

Two endpoints, no models, no billing. Snapping is deterministic and reaches no
AI provider, so it goes nowhere near ``ai_debit_credits`` and nowhere near
``credits.services``: it is free, like every other deterministic path
(SCOPE_road_routing.md@8914275 §8.3, restated as
SCOPE_routing_sandbox_external.md@c170e1a D9 — the external quota is a *capacity* limit,
not a price). A test reads this module's source to keep it that way.

**Both endpoints are ``auth=None``, and on migratis.ai /snap is no longer open.**
One file, two postures, chosen by a setting rather than by forking this module —
which is the only way a divergence survives in an app that is copied verbatim
into base.

The original justification still holds for an **installed app**: the sandbox is
public by design, and a generated app may let an anonymous role create records —
a login-gated snap would mean the map editor works for the owner and silently
draws straight lines for everyone else. Its engine is its own, free and
stateless, so there is no quota for a stranger to exhaust. Base names no
authorizer and no ceiling, and behaves exactly as it did before this scope.

**On migratis.ai half of that died with D3′.** A generated app no longer calls
migratis's ``/snap`` at all; it calls its own. The only legitimate caller of
that copy is the migratis sandbox, and it now stands in front of a metered quota
belonging to someone else — one scraper would end sandbox routing for every user
until the window resets. So three things guard it there, in order of value (§6):

1. ``ROUTING_SNAP_AUTHORIZER`` — a callable named in settings that says whether
   this caller may snap at all. On migratis it asks for a valid sandbox token,
   which keeps *anonymous* sandbox visitors working while closing the tap. It is
   reached through a setting and not an import because ``routing`` must never
   import ``generator`` (§5.6): it is base-syncable and installable alone, and
   the tell that the rule is being broken is something here needing to ask what
   an ``Application`` references.
2. ``throttle`` — bounds a caller who *does* hold a link. Off by default; only
   the deployment in front of a meter turns it on.
3. ``breaker`` (inside the adapter) — stops rejected calls becoming outbound
   ones.

``MAX_WAYPOINTS`` and the range checks still run before any network call, the
engine URL still comes from settings and never from the request (no SSRF),
nothing is written and nothing is charged.
"""
from functools import lru_cache

from django.conf import settings
from django.http import JsonResponse
from django.utils.module_loading import import_string
from ninja import Router

from . import engines, services, throttle
from .schemas import SnapIn

router = Router()


def _detail(key, message):
    return [{'loc': ['routing'], 'msg': key, 'type': message}]


@lru_cache(maxsize=8)
def _load_authorizer(path):
    """Resolve the dotted path once. Cached on the path, so an override in a
    test still resolves and a production process does not re-import per call."""
    return import_string(path)


def _may_snap(request):
    """Whether this caller may reach the engine.

    Absent setting → open, which is base's posture and the original behaviour.
    Present but unimportable → **closed**: a typo in a setting must not silently
    reopen the tap in front of someone else's metered quota.
    """
    path = (getattr(settings, 'ROUTING_SNAP_AUTHORIZER', '') or '').strip()
    if not path:
        return True
    try:
        authorize = _load_authorizer(path)
    except ImportError:
        return False
    return bool(authorize(request))


@router.post('/snap', auth=None)
def snap(request, payload: SnapIn):
    """Waypoints + profile → road-following geometry (§4 shape).

    Every failure is *named*. The caller keeps whatever line the user traced and
    badges it with the reason; it never discards the edit and never presents a
    straight line as if it followed roads.
    """
    if not _may_snap(request):
        # Checked before the throttle: a caller with no standing never touches
        # the counters, so a stranger in a loop cannot exhaust a real user's
        # bucket by sharing their address.
        return JsonResponse({'detail': _detail('routing-snap-forbidden',
                                               'snap-forbidden')}, status=403)
    if not throttle.allow(request):
        # 429 rather than 503: the engine is fine, this caller is not. The
        # frontend reads any unnamed status as "unavailable" and keeps the edit,
        # which is the right behaviour here too — the line is not a road route
        # and must not claim to be.
        return JsonResponse({'detail': _detail('routing-rate-limited',
                                               'rate-limited')}, status=429)

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
        # and neither does a quota stop, so no hostname, internal address or
        # account state can ride out on it.
        return JsonResponse({'detail': _detail('route-not-found', 'no-route'),
                             'engine_reason': str(exc)[:200]}, status=422)
    except engines.EngineUnavailable as exc:
        # Told apart so the UI can hide the affordance in one case and badge it
        # in the other. The engine's text is deliberately dropped — this is the
        # branch a spent quota arrives on, and an ORS error body quotes API keys.
        key = ('routing-engine-not-configured' if str(exc) == 'not-configured'
               else 'routing-engine-unavailable')
        return JsonResponse({'detail': _detail(key, 'engine-unavailable')}, status=503)

    return JsonResponse(geometry)


@router.get('/availability', auth=None)
def availability(request):
    """Whether waypoint mode should be offered at all, measured now.

    Read once by the map editor, and **not gated**: it is what tells the editor
    whether to offer waypoint mode, so closing it would hide the feature from
    the very page that is allowed to use it. It aims no metered call either —
    the adapter caches its probe and the breaker sits in front of it.

    ``not_configured`` means the feature was never asked for on this host, so
    nothing is shown and no error is raised; ``unavailable`` means it was asked
    for and is down — including a spent quota, which is a capacity problem and
    never a claim that the user's route is impossible (§5.4). Never publishes
    the engine's error, same rule as the AI breaker reason.
    """
    state, engine_name = services.engine_state()
    return JsonResponse({
        'available': state == 'operational',
        'state':     state,
        'engine':    engine_name,
        'profiles':  list(services.ROUTE_PROFILES),
    })
