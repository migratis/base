"""A setting read through `getattr` must be a setting `settings.py` defines.

`migratis/installer/views.py` gated its package endpoints like this:

    token = (getattr(settings, 'INSTALLER_AGENT_TOKEN', '') or '').strip()
    if token:                      # unreachable
        ...X-Installer-Token auth...
    return request.META.get('REMOTE_ADDR', '') in ('127.0.0.1', '::1', ...)

`settings.py` never named `INSTALLER_AGENT_TOKEN`, so the `getattr` fell to
`''` on every call and the header branch was dead code. The endpoints stayed
loopback-only however the operator configured them — and the operator HAD
configured them: the token sat in `backend/migratis/.env` being read by
nothing, while the 403's own text, the agent guide and the README all went on
describing a header that could not work. An off-box agent found it by failing
to install.

The `getattr` default is what makes this silent. A bare
`settings.INSTALLER_AGENT_TOKEN` raises the first time the code runs; with a
default, a knob nobody can turn is indistinguishable from a knob left at its
default. That is why this is checked statically rather than at the call site:
by the time the call happens there is nothing left to observe.

Base's convention makes the rule exact. `settings.py` declares every module
knob unconditionally with an env-backed default (`ROUTING_ENGINE_URL`,
`DATASOURCE_BREAKER_SECONDS`, …) whether or not the module is installed, and
then execs `settings_patches/*.py` at the end so a generated app can add more.
So "defined" means the resolved `settings` object has the attribute — a
patch-provided name counts — and no installed-app scoping is needed. That
matters: `routing` and `subscription` are not installed on most bases, and the
three gaps this check first reported were all in modules that were not.

Scope is `migratis/` — the framework's own tree. An installed application at
`backend/<module>/` reads settings its own `settings_patch.py` writes, which is
its business and not this template's.

Reported as a Warning, not an Error. The code still runs: it runs on the
default forever, which is a configurability defect rather than a crash, and a
base that refuses to boot over one is worse than the bug. `manage.py check` is
where it surfaces, which is already this project's smoke test.
"""
import ast
import os

from django.conf import settings
from django.core.checks import Warning as CheckWarning, register

_SKIP_DIRS = {'migrations', '__pycache__', 'backups', 'node_modules', '.git'}


def _setting_reads(path):
    """`(name, lineno)` for each `getattr(<…>settings, 'NAME', <default>)`.

    Only the three-argument form with a literal name: two arguments raise on a
    missing setting and are therefore self-reporting, and a computed name
    (`getattr(settings, name, '')`, as the datasource registry and both
    throttles use to build a per-provider key) cannot be resolved from the
    source at all.
    """
    try:
        with open(path, encoding='utf-8') as fh:
            tree = ast.parse(fh.read(), filename=path)
    except (OSError, SyntaxError):       # unreadable or not importable anyway
        return
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name) and node.func.id == 'getattr'
                and len(node.args) == 3):
            continue
        target, name = node.args[0], node.args[1]
        # `settings`, `django_settings`, `conf_settings` — the aliases this
        # tree actually imports it under.
        if not (isinstance(target, ast.Name) and target.id.endswith('settings')):
            continue
        if isinstance(name, ast.Constant) and isinstance(name.value, str):
            yield name.value, node.lineno


@register()
def check_settings_reads_are_declared(app_configs, **kwargs):
    """Every framework setting read with a default is one settings.py names."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # migratis/
    findings, seen = [], set()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        for filename in sorted(filenames):
            if not filename.endswith('.py'):
                continue
            path = os.path.join(dirpath, filename)
            for name, lineno in _setting_reads(path):
                if hasattr(settings, name) or (name, path) in seen:
                    continue
                seen.add((name, path))
                findings.append(CheckWarning(
                    f"{os.path.relpath(path, root)}:{lineno} reads "
                    f"settings.{name}, which is never defined.",
                    hint=(f"The getattr default is used unconditionally, so "
                          f"{name} cannot be configured — setting it in "
                          f"backend/migratis/.env does nothing. Declare it in "
                          f"migratis/settings.py beside its module's other "
                          f"knobs, e.g. "
                          f"`{name} = env('{name}', default=...)`."),
                    id='migratis.W001',
                ))
    return findings
