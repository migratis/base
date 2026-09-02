"""Who we refuse to talk to on purpose.

SCOPE_external_data_sources.md@d2de531 §8.1a, decision **D14**. The owner's
choice is a **denylist filled over time**, not an allowlist curated in advance:
an allowlist makes the owner the bottleneck for every new API any user wants,
and a bare `DATASOURCE_ALLOWED_HOSTS=''` records no policy at all.

Reading "default open" as "no checks" would be exactly backwards. The address
checks in `addresses.py` decide **where the packet actually goes**; this decides
**who we refuse to talk to on purpose**, and neither substitutes for the other.
Nor does either substitute for §5.6's staff review, which is the *proactive*
gate for adapters other applications can fork while this is the *reactive* gate
for everything else.

Four properties, and the first three are the whole of the design:

* **Editable without a deploy.** A list in `settings.py` is a list nobody adds
  to at 23:00 on the day it is needed — the same argument that moved the LLM
  catalog out of settings into `LLMProvider`/`LLMModel`. So the policy is a
  dotted path (`DATASOURCE_HOST_POLICY`) resolving to `(host) -> allowed`,
  exactly as `routing` reaches its authorizer. On migratis it points at a
  `generator`-side function over a `DeniedHost` table; base names none and
  denies nothing, and `datasource` still never imports `generator` and still
  owns no models.
* **Retroactive.** This runs at the gate *and on every call*, so a host denied
  this afternoon stops working this afternoon — including for adapters approved
  last month and every application that forked one. A denylist that only bound
  new declarations would refuse exactly the hosts nobody has used yet.
* **Loud.** The retirement and the `datasource_adapter_host_denied` advisory
  live on the `generator` side, where there is an `Application` to raise them
  against.
* **Subdomains and normalisation.** `evil.example` that does not also refuse
  `api.evil.example` refuses nothing — one DNS record is not a barrier.

`DATASOURCE_DENIED_HOSTS` survives as the static fallback for a deployment with
no policy callable.
"""
from functools import lru_cache

from django.conf import settings
from django.utils.module_loading import import_string

from .hosts import host_matches, normalise_host


@lru_cache(maxsize=8)
def _load(path):
    """Resolve the dotted path once, cached on the path — so an override in a
    test still resolves and a production process does not re-import per call."""
    return import_string(path)


def _static_denied():
    raw = getattr(settings, 'DATASOURCE_DENIED_HOSTS', '') or ''
    if isinstance(raw, str):
        entries = [e.strip() for e in raw.replace('\n', ',').split(',')]
    else:
        entries = [str(e).strip() for e in raw]
    return [e for e in entries if e]


def host_allowed(host):
    """Whether a request may be sent to `host`.

    Absent setting → the static fallback, which is empty by default: **open**.
    Present but unimportable → **closed**. A typo in a setting must not silently
    switch a deny policy off, which is `routing`'s reading of the same situation
    one module over.
    """
    normalised = normalise_host(host)
    if not normalised:
        return False
    path = (getattr(settings, 'DATASOURCE_HOST_POLICY', '') or '').strip()
    if path:
        try:
            policy = _load(path)
        except ImportError:
            return False
        return bool(policy(normalised))
    return not any(host_matches(normalised, entry) for entry in _static_denied())
