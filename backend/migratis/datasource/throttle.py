"""Bounding a caller who is allowed to call, and the owner's daily meter.

SCOPE_external_data_sources.md@d2de531 §8.3. Routing's problem was a stranger
burning *the platform's* ORS allowance. Here a stranger burns *the owner's* key,
on the owner's bill, through a sandbox link that is public by design — so there
are two counters rather than one, and they answer different questions:

* `allow(request)` — per client address, per minute. Bounds someone who has the
  link and a loop. Off by default (0), as `routing/throttle.py`: the deployment
  standing in front of a meter is the one that turns it on.
* `consume_daily(application_id)` — per **application**, per day. New, because
  the meter is the owner's and the per-caller ceiling does nothing against a
  hundred callers.

Exhausting the daily ceiling is `datasource-quota-exhausted` and **never** an
empty candidate list. An empty list that actually means *you have run out* is
the `route-not-found`-vs-`routing-engine-unavailable` mistake in a new module.

Both live in the cache, because this module owns no models (§3.1). Per-process,
therefore approximate, therefore sized under the real limit rather than at it —
routing's caveat, unchanged.
"""
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

DEFAULT_PER_MINUTE   = 0        # off unless an operator asks
DEFAULT_DAILY_PER_APP = 500     # a designer filling forms, not a crawler


def client_ip(request):
    """The caller's address as far as this deployment can honestly tell.

    `X-Real-IP` is *set* by nginx, not appended to, so a client cannot choose its
    own bucket by sending one; `REMOTE_ADDR` is the fallback for a stack with no
    proxy in front.
    """
    meta = getattr(request, 'META', None) or {}
    return (meta.get('HTTP_X_REAL_IP') or meta.get('REMOTE_ADDR') or 'unknown').strip()


def _int_setting(name, default):
    try:
        return int(getattr(settings, name, default))
    except (TypeError, ValueError):
        return default


def _bump(key, ttl):
    """One more use of `key`, returned. `add` first, so two threads arriving
    together cannot both initialise the counter and lose one of the increments."""
    cache.add(key, 0, ttl)
    try:
        return cache.incr(key)
    except ValueError:
        # The bucket expired between the add and the incr — a new window with one
        # call in it, not a reason to refuse.
        cache.set(key, 1, ttl)
        return 1


def allow(request):
    """True when this caller may make one more lookup this minute."""
    limit = _int_setting('DATASOURCE_RATE_PER_MINUTE', DEFAULT_PER_MINUTE)
    if limit <= 0:
        return True
    key = f'datasource:rate:{client_ip(request)}:{timezone.now().strftime("%Y%m%d%H%M")}'
    return _bump(key, 120) <= limit


def consume_daily(application_id):
    """Spend one of this application's daily lookups. False when it has run out.

    Counted at the point the outbound call is about to be made, not on the way
    back: a refused source still costs the owner a request against their rate
    limit, and pretending otherwise is how a dead key spends a whole day's
    allowance in a loop.
    """
    limit = _int_setting('DATASOURCE_DAILY_PER_APPLICATION', DEFAULT_DAILY_PER_APP)
    if limit <= 0:
        return True
    key = f'datasource:daily:{application_id}:{timezone.now().strftime("%Y%m%d")}'
    return _bump(key, 86400 + 3600) <= limit


def daily_used(application_id):
    key = f'datasource:daily:{application_id}:{timezone.now().strftime("%Y%m%d")}'
    return cache.get(key) or 0
