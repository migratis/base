"""Whether this caller may spend one of somebody's lookups.

SCOPE_external_data_sources.md@d2de531 §8.3 item 1. `DATASOURCE_AUTHORIZER` is a
dotted path in settings, resolved here, for the reason `routing` has already
worked twice: this module is base-syncable and installable alone and **must
never import `generator`** — it has never heard of an `Application` and cannot
ask whether a caller is inside a sandbox we published.

Absent setting → **open**, which is base's posture: an installed app's endpoint
calls the owner's own key against a quota the owner chose, and a generated app
may let an anonymous role create records, so gating it there would mean the
lookup works for the owner and silently does nothing for everyone else.

Present but unimportable → **closed**. A typo in a setting must not silently
reopen a tap in front of somebody's metered key.
"""
from functools import lru_cache

from django.conf import settings
from django.utils.module_loading import import_string


@lru_cache(maxsize=8)
def _load(path):
    return import_string(path)


def may_lookup(request, **context):
    """True when `request` may run a lookup. `context` carries whatever the
    authorizer needs and this module must not interpret — the sandbox token, the
    entity name, the application id."""
    path = (getattr(settings, 'DATASOURCE_AUTHORIZER', '') or '').strip()
    if not path:
        return True
    try:
        authorize = _load(path)
    except ImportError:
        return False
    return bool(authorize(request, **context))
