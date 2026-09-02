"""A local stop in front of a source that is refusing us.

SCOPE_external_data_sources.md@d2de531 §8.3 item 3, the `routing/breaker.py`
pattern with one difference that matters: routing's breaker guards **the
platform's** allowance, and this one guards **the owner's**. A source answering
401 all morning must stop being called, because every one of those calls is a
row on somebody's bill and a step towards their rate limit.

Keyed per (application, adapter) rather than per host: two applications binding
the same public adapter hold different keys, and one owner's dead key must not
switch the source off for the other.

Like routing's, it lives in the **cache** because `migratis.datasource` owns no
models on purpose (§3.1) — the moment it has a table it has migrations every
installed app has to carry for a feature most of them never enable. The cost is
the same and is stated rather than hidden: the default cache is per-process, so
with three workers the breaker trips per worker. That weakens the bound, never
the guarantee.

**The reason is stored and never published.** A provider's error body quotes API
keys and account states — the same rule that keeps the AI breaker's reason off
/status.
"""
from django.conf import settings
from django.core.cache import cache

DEFAULT_SECONDS = 300
MIN_SECONDS     = 60
MAX_SECONDS     = 3600


def _key(scope):
    return f'datasource:breaker:{scope}'


def scope_key(application_id, adapter_slug):
    """The identity a breaker trips for: this application's use of this adapter."""
    return f'{application_id or "0"}:{adapter_slug or ""}'


def _window(seconds=None):
    if seconds is None:
        seconds = getattr(settings, 'DATASOURCE_BREAKER_SECONDS', DEFAULT_SECONDS)
    try:
        return max(MIN_SECONDS, min(MAX_SECONDS, int(seconds)))
    except (TypeError, ValueError):
        return DEFAULT_SECONDS


def trip(scope, reason='', seconds=None):
    cache.set(_key(scope), reason or 'refused', _window(seconds))


def is_tripped(scope):
    return cache.get(_key(scope)) is not None


def reason(scope):
    """The stored text. For a `docker logs` — never for a response body."""
    return cache.get(_key(scope)) or ''


def reset(scope):
    cache.delete(_key(scope))
