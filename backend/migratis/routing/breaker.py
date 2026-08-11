"""A local stop in front of a metered engine.

SCOPE_routing_sandbox_external.md@c170e1a §6 item 3. Migratis' own Valhalla was free,
stateless and ours; openrouteservice is none of those. Against a metered quota,
forty rejected calls a minute must not become forty *outbound* calls a minute —
the provider counts the rejections too, and a stack that keeps knocking is a
stack that never gets its window back.

This is the ``AIServiceState`` pattern without the billing, and without the
model. ``migratis.routing`` owns no models on purpose (§5.6): it is
base-syncable and installable alone, and the moment it has a table it has
migrations that every installed app has to carry for a feature most of them
never enable. The breaker's whole lifetime is a few minutes, which is exactly
what a cache is for.

The cost of that choice, stated rather than hidden: the default cache is
per-process, so with three gunicorn workers the breaker trips per worker. That
weakens the *bound* (three probes instead of one before every worker gives up)
and not the *guarantee* — no worker floods, and none of them charges anything.
Sizing follows from it: ``ROUTING_SNAP_RATE_PER_MINUTE`` is set well under the
provider's own window rather than at it.

**The reason is stored and never published.** It is here so a `docker logs` can
answer "why is routing off", and an ORS error body can quote an API key or an
account state — the same rule that keeps the AI breaker's reason off /status.
"""
from django.conf import settings
from django.core.cache import cache

# The window a provider hands back. ORS meters both a 40/min sliding window and
# a daily quota, and a 429 does not say which — so the stop is long enough to be
# worth having and short enough that a per-minute throttle is not treated as a
# day-long outage.
DEFAULT_SECONDS = 300
MIN_SECONDS     = 60
MAX_SECONDS     = 3600


def _key(engine_name):
    return f'routing:breaker:{engine_name}'


def _window():
    seconds = getattr(settings, 'ROUTING_BREAKER_SECONDS', DEFAULT_SECONDS)
    try:
        return max(MIN_SECONDS, min(MAX_SECONDS, int(seconds)))
    except (TypeError, ValueError):
        return DEFAULT_SECONDS


def trip(engine_name, reason='', seconds=None):
    """Stop calling ``engine_name`` for a while.

    ``seconds`` lets an adapter honour a reset hint the provider sent
    (``X-Ratelimit-Reset``); it is clamped, because a header is a value from
    someone else's host and a bad one would either flap or switch routing off
    for a week.
    """
    window = _window() if seconds is None else max(MIN_SECONDS, min(MAX_SECONDS, int(seconds)))
    cache.set(_key(engine_name), reason or 'quota', window)


def is_tripped(engine_name):
    return cache.get(_key(engine_name)) is not None


def reason(engine_name):
    """The stored text. For a log line — never for a response body."""
    return cache.get(_key(engine_name)) or ''


def reset(engine_name):
    cache.delete(_key(engine_name))
