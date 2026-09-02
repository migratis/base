"""The declarations a generated application carries, loaded from a file.

SCOPE_external_data_sources.md@d2de531 §3.1. **The generated app cannot read a
table that does not exist there**: every declaration lives in `generator`, and
this module owns no models and must never import `generator`. So codegen emits
the resolved declarations as `backend/<module>/datasources.json` and this loads
them from `settings.DATASOURCE_DECLARATIONS` — the same shape as
`ROUTING_TILE_URLS` arriving as a plain value, one level up in structure because
a declaration is not a string.

**Credentials are not in the file** (D12). It names the header a key travels
under and the env var the installer wrote it to; the value is read from settings
at call time and never appears in the package, the manifest or a log.

On migratis itself the setting is unset and this loads nothing: the sandbox
reads the real rows, and this path exists only in the installed world.
"""
import json
import logging
from pathlib import Path

from django.conf import settings

from .mapping import AdapterSpec, BindingSpec

logger = logging.getLogger(__name__)

_CACHE = {}


def _path():
    return (getattr(settings, 'DATASOURCE_DECLARATIONS', '') or '').strip()


def _load():
    """`{'adapters': {...}, 'bindings': {...}}`, cached per file path.

    A missing or unreadable file is **empty, never an exception**: an
    application that declares no source is the ordinary case, and a malformed
    file must take the lookups away rather than the whole app.
    """
    path = _path()
    if not path:
        return {'adapters': {}, 'bindings': {}}
    if path in _CACHE:
        return _CACHE[path]
    try:
        raw = json.loads(Path(path).read_text())
    except (OSError, ValueError) as exc:
        logger.warning('[DATASOURCE] Could not read %s: %s', path, exc)
        raw = {}
    adapters = {slug: AdapterSpec.from_dict(data)
                for slug, data in (raw.get('adapters') or {}).items()}
    credential_settings = {slug: (data.get('credential_setting') or '')
                           for slug, data in (raw.get('adapters') or {}).items()}
    bindings = {}
    for data in (raw.get('bindings') or []):
        key = data.get('key') or f"{data.get('entity')}.{data.get('adapter_slug')}"
        bindings[key] = BindingSpec.from_dict(data)
    loaded = {'adapters': adapters, 'bindings': bindings,
              'credential_settings': credential_settings}
    _CACHE[path] = loaded
    return loaded


def reset():
    """Forget the cache — for tests, and for an installer that just rewrote it."""
    _CACHE.clear()


def binding(key):
    return _load()['bindings'].get(key)


def adapter_for(binding_spec):
    return _load()['adapters'].get(binding_spec.adapter_slug) if binding_spec else None


def bindings_for_entity(entity_name):
    return [b for b in _load()['bindings'].values() if b.entity == entity_name]


def credential_for(adapter_spec):
    """The key for this adapter, from the deployment's own settings.

    `DATASOURCE_<SLUG>_KEY` (D11), read at call time and nowhere stored by this
    module. Absent is '' — a keyless adapter and an unconfigured one both simply
    send no key, and the difference is a question for the installer's
    `datasource_key_required` notice, not for the socket.
    """
    if adapter_spec is None:
        return ''
    slug = (adapter_spec.slug or '').upper()
    name = _load()['credential_settings'].get(adapter_spec.slug) or \
        f'DATASOURCE_{slug}_KEY'
    return (getattr(settings, name, '') or '').strip()


def missing_credential_settings():
    """The env var names an operator still has to fill. For a status surface."""
    missing = []
    for slug, spec in _load()['adapters'].items():
        if spec.auth_mode == 'none':
            continue
        if not credential_for(spec):
            missing.append(_load()['credential_settings'].get(slug)
                           or f'DATASOURCE_{slug.upper()}_KEY')
    return sorted(set(missing))
