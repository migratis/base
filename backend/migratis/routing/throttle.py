"""Bounding a caller who is allowed to call.

SCOPE_routing_sandbox_external.md@c170e1a §6 item 2. The sandbox-token gate stops a
stranger; this stops someone who has a public sandbox link and a loop. The two
are ordered by value on purpose — throttling alone would still hand the whole
quota to whoever asks first, and the gate alone would still let one link burn
the day's allowance.

Counted per client address, in the cache, for the reason spelled out in
``breaker``: this module owns no models. The same per-process caveat applies,
which is why migratis sets a limit well under openrouteservice's own 40/min
window rather than at it.

**Off unless an operator asks.** The code default is 0 — no ceiling — because
the deployment this module was written for first is an installed app calling a
Valhalla its owner runs: free, stateless, theirs, and throttling it would only
take a working feature away from an anonymous role that is allowed to use it.
migratis.ai sets ``ROUTING_SNAP_RATE_PER_MINUTE`` in its own settings, because
it is the deployment standing in front of somebody else's meter. Which is the
shape of every divergence in this app: a setting, never a fork of the code.
"""
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

DEFAULT_PER_MINUTE = 0


def client_ip(request):
    """The caller's address as far as this deployment can honestly tell.

    ``X-Real-IP`` is *set* by nginx (``proxy_set_header X-Real-IP
    $remote_addr``), not appended to, so a client cannot choose its own bucket
    by sending one. ``REMOTE_ADDR`` is the fallback for a deployment with no
    proxy in front — a local stack, or an installed app someone runs directly.
    """
    meta = getattr(request, 'META', None) or {}
    return (meta.get('HTTP_X_REAL_IP') or meta.get('REMOTE_ADDR') or 'unknown').strip()


def _limit():
    try:
        return int(getattr(settings, 'ROUTING_SNAP_RATE_PER_MINUTE', DEFAULT_PER_MINUTE))
    except (TypeError, ValueError):
        return DEFAULT_PER_MINUTE


def allow(request):
    """True when this caller may make one more snap this minute.

    A fixed minute bucket rather than a sliding window: the sliding version
    needs a list per caller and this needs an integer, and the failure it guards
    against is a loop, not a burst of two.
    """
    limit = _limit()
    if limit <= 0:
        return True                       # explicitly switched off by an operator
    key = f'routing:snap:{client_ip(request)}:{timezone.now().strftime("%Y%m%d%H%M")}'
    # `add` only writes when the key is absent, so two threads arriving together
    # cannot both initialise the counter and lose one of the increments.
    cache.add(key, 0, 120)
    try:
        used = cache.incr(key)
    except ValueError:
        # The bucket expired between the add and the incr — that is a new minute
        # with one call in it, not a reason to refuse.
        cache.set(key, 1, 120)
        used = 1
    return used <= limit
