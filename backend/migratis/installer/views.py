"""
installer/views.py
------------------
Endpoints that proxy auth to a remote Migratis generator instance,
list the user's generated applications, download them and install
the backend portion directly into this base project.

Endpoints (all under /backend/api/installer/):
    POST   /connect              — authenticate against Migratis, store session
    DELETE /connect              — clear stored session
    GET    /session              — check whether a session is stored
    GET    /apps                 — list generated apps from Migratis
    POST   /install/{id}         — download ZIP + apply backend files + migrate
    GET    /frontend-zip/{id}    — stream frontend-only ZIP for manual extraction
    GET    /installed            — list modules currently installed in this project
    POST   /uninstall/{module}   — remove a previously installed module
    POST   /upgrade/{id}/preview — dry-run: the changes an upgrade would apply
    POST   /upgrade/{id}         — upgrade an installed module keeping its data

Design: the installer never patches settings.py, api/views.py, App.js, or
MenuLeft.js. Instead it:
  - Writes  settings_patches/<module>.py        → auto-exec'd by settings.py
  - Writes  settings_patches/<module>_additions.json  → source for registry
  - Rewrites frontend/src/module_registry.js   → consumed by App.js + MenuLeft.js
"""

import io
import json
import os
import re
import shutil
import subprocess
import zipfile
from datetime import datetime, timedelta, timezone as dt_timezone
from pathlib import Path

import requests as http_requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from ninja import Router

router = Router()

MIGRATIS_BACKEND_URL = getattr(settings, 'MIGRATIS_BACKEND_URL', 'http://host.docker.internal:8000')

# Migratis' trusted-device cookie: once a 2FA code is verified with
# remember_device, Migratis sets this cookie and subsequent logins skip 2FA for
# TRUST_DAYS. The installer talks to Migratis over a fresh server-side
# requests.Session per connect, so it must persist this cookie itself and replay
# it on login — otherwise every connect re-prompts for a code. Mirrors
# migratis.user.views.TFA_COOKIE_NAME / TFA_COOKIE_DURATION.
MIGRATIS_TFA_COOKIE     = 'tfa_verified'
MIGRATIS_TFA_TRUST_DAYS = 7

_FRAMEWORK_MODULES = frozenset([
    'user', 'i18n', 'cookie', 'support', 'subscription', 'generator', 'installer',
])

# Framework routers that modules may activate in api/views.py. Each tuple is
# (app key, router var name, views module path, mount path). i18n and cookie are
# always-on in the base project; the rest are toggled by install/uninstall.
_FRAMEWORK_ROUTERS = [
    ('user',         'user_router',         'migratis.user.views',         '/user/'),
    ('i18n',         'i18n_router',         'migratis.i18n.views',         '/i18n/'),
    ('cookie',       'cookie_router',       'migratis.cookie.views',       '/cookie/'),
    ('support',      'support_router',      'migratis.support.views',      '/support/'),
    ('subscription', 'subscription_router', 'migratis.subscription.views', '/subscription/'),
]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _session(request):
    cookies  = request.session.get('migratis_cookies')
    base_url = request.session.get('migratis_url', MIGRATIS_BACKEND_URL)
    if not cookies:
        return None, base_url
    s = http_requests.Session()
    s.cookies.update(cookies)
    return s, base_url


def _err(key, msg):
    return JsonResponse({'detail': [{key: [msg]}]}, status=400)


def _clear_migratis_session(request):
    """Drop the stored Migratis session cookies after the upstream rejects them.
    Keeps `migratis_url` so the login form can prefill the instance. This makes
    /session report disconnected, so the UI shows login instead of failures."""
    request.session.pop('migratis_cookies', None)
    request.session.modified = True


def _session_expired_response():
    return JsonResponse({'detail': [{'session': ['not-connected']}]}, status=401)


def _backend_autoreloads() -> bool:
    """True when the Django dev server's autoreloader is active, so rewriting
    api/views.py (done last in _apply_package) restarts the worker automatically
    and the deferred migrate runs on its own — no manual restart needed. The
    autoreloader runs the request-handling worker with RUN_MAIN=true; production
    WSGI servers (gunicorn/uwsgi behind nginx) do not set it, so a restart is
    required there."""
    return os.environ.get('RUN_MAIN') == 'true'


def _patches_dir(backend_root: Path) -> Path:
    return backend_root / 'settings_patches'


def _volume_owner(backend_root: Path):
    """Return (uid, gid) of the backend volume root — i.e. the host user."""
    st = backend_root.stat()
    return st.st_uid, st.st_gid


def _chown_tree(path: Path, uid: int, gid: int):
    """Recursively chown path to uid:gid."""
    try:
        os.chown(path, uid, gid)
        if path.is_dir():
            for child in path.rglob('*'):
                try:
                    os.chown(child, uid, gid)
                except OSError:
                    pass
    except OSError:
        pass


def _fix_backend_py(content: bytes, module: str, name: str = '') -> bytes:
    """
    Normalise known AI slip-ups in generated backend Python before it lands
    on disk:
      - `backend.<module>` dotted paths (`backend/` is the working directory,
        not a package) — in apps.py this crashes the whole app registry at
        the next reload. Targeted to the module name so legitimate strings
        are never touched; migration files keep the broader historical fix.
      - `from ninja.files import File` → `from ninja import File`.
    """
    if '/migrations/' in name:
        content = content.replace(b'backend.', b'')
    else:
        content = content.replace(
            f'backend.{module}'.encode(), module.encode(),
        )
    return content.replace(
        b'from ninja.files import File',
        b'from ninja import File',
    )


def _validate_package_python(zf, module: str) -> list:
    """
    Pre-flight: compile-check every backend .py in the package (after the
    same _fix_backend_py transforms that would land on disk). Returns a list
    of '<path>: line N: <msg>' strings — non-empty means the package must NOT
    be applied: writing a syntactically broken views.py/models.py crashes the
    running app at the next autoreload (app-8 v6 shipped an annotated lambda).
    """
    errors = []
    for name in zf.namelist():
        if not (name.startswith('backend/') and name.endswith('.py')):
            continue
        content = _fix_backend_py(zf.read(name), module, name)
        try:
            compile(content.decode('utf-8', errors='replace'), name, 'exec')
        except SyntaxError as exc:
            errors.append(f'{name}: line {exc.lineno}: {exc.msg}')
    return errors


def _get_installed_modules(backend_root: Path) -> list:
    """Return modules that correspond to an actually-installed app — i.e. a
    settings_patches/<module>.py paired with a <module>_manifest.json. Managed
    internal patches (e.g. zzz_language.py, written by _write_language_patch) have
    no manifest, so they are not mistaken for installed apps."""
    d = _patches_dir(backend_root)
    if not d.exists():
        return []
    return sorted(
        p.stem for p in d.glob('*.py')
        if p.stem != '__init__'
        and p.stem not in _FRAMEWORK_MODULES
        and (d / f'{p.stem}_manifest.json').exists()
    )


def _module_name(name: str) -> str:
    """Mirror Migratis' generator module-name derivation so installed apps can be
    matched against the remote app list (which doesn't expose the module name)."""
    return (name or '').lower().replace(' ', '_').replace('-', '_')


def _rebuild_registry(backend_root: Path, frontend_root: Path):
    """
    Regenerate module_registry.js from all *_additions.json files
    in settings_patches/. Called after every install and uninstall.

    Menu items keep their `min_list_role` and the per-module role ladder
    (from the manifest) is exported as `moduleRoles`, so MenuLeft can hide
    entries the viewer's role may not list — the same navigation rule the
    sandbox applies. Dropping these here was why anonymous visitors saw
    every entity tab.
    """
    registry_path = frontend_root / 'module_registry.js'
    if not registry_path.exists():
        return  # frontend volume not mounted

    # Match the leading `const X = lazyWithRetry(() => import('path')` prefix
    # only — newer generator output appends a `.then(m => ({ default: ... }))`
    # named→default coercion (AI containers use named exports), so anchoring the
    # whole line with `$` silently dropped every import. We capture name + path
    # for the module separator / routes and keep the original statement verbatim
    # so the coercion survives.
    import_re = re.compile(
        r"^const (\w+) = lazyWithRetry\(\(\) => import\('([^']+)'\)"
    )
    route_re = re.compile(r'path="([^"]+)"[^>]*element=\{<(\w+)\s*/?>}')

    all_imports = []   # [(component_name, import_path, statement), ...]
    all_routes  = []   # [(url_path, component_name), ...]
    all_menu    = []   # [{"label", "path", "min_list_role", "module"}, ...]
    all_roles   = {}   # {module: {ranks, anonymous, default_auth, privileged}}

    patches_dir = _patches_dir(backend_root)
    for additions_file in sorted(patches_dir.glob('*_additions.json')):
        additions = json.loads(additions_file.read_text())
        module    = additions.get('module', additions_file.stem.replace('_additions', ''))

        for imp in additions.get('imports', []):
            stmt = imp.strip()
            m = import_re.match(stmt)
            if m:
                all_imports.append((m.group(1), m.group(2), stmt))

        for route in additions.get('routes', []):
            m = route_re.search(route)
            if m:
                all_routes.append((m.group(1), m.group(2)))

        for item in additions.get('menu_items', []):
            all_menu.append({
                'label':         item.get('label', ''),
                'path':          item.get('path', ''),
                'min_list_role': item.get('min_list_role', ''),
                'module':        module,
            })

        # Role ladder from the module's manifest — same derivation as the
        # generated roles.py (anonymous tier, lowest non-anonymous default,
        # highest rank privileged).
        manifest = _read_installed_manifest(backend_root, module) or {}
        roles    = manifest.get('roles') or []
        if roles:
            all_roles[module] = {
                'ranks':        {r['name']: r['rank'] for r in roles},
                'anonymous':    next((r['name'] for r in roles if r.get('is_anonymous')),
                                     roles[0]['name']),
                'default_auth': next((r['name'] for r in roles if not r.get('is_anonymous')),
                                     roles[-1]['name']),
                'privileged':   roles[-1]['name'],
            }

    lines = []
    if all_imports:
        lines.append("import { lazyWithRetry } from './common/tools/lazyWithRetry';")
        lines.append('')
        prev_module = None
        for name, imp_path, stmt in all_imports:
            # Add a comment separator when the module changes
            module_guess = imp_path.split('/')[1] if imp_path.startswith('./') else ''
            if module_guess != prev_module:
                lines.append(f"// ── {module_guess} ──")
                prev_module = module_guess
            # Emit verbatim so the named→default coercion (.then(...)) survives.
            lines.append(stmt if stmt.endswith(';') else stmt + ';')
        lines.append('')

    routes_js = ',\n  '.join(
        f'{{ path: "{p}", Component: {c} }}' for p, c in all_routes
    ) if all_routes else ''
    lines.append(f"export const moduleRoutes = [{f'{chr(10)}  {routes_js},{chr(10)}' if routes_js else ''}];")
    lines.append('')

    menu_js = ',\n  '.join(
        f'{{ label: "{item["label"]}", path: "{item["path"]}", '
        f'min_list_role: "{item["min_list_role"]}", module: "{item["module"]}" }}'
        for item in all_menu
    ) if all_menu else ''
    lines.append(f"export const moduleMenuItems = [{f'{chr(10)}  {menu_js},{chr(10)}' if menu_js else ''}];")
    lines.append('')
    lines.append(f"export const moduleRoles = {json.dumps(all_roles, indent=2)};")
    lines.append('')

    registry_path.write_text('\n'.join(lines))


# --------------------------------------------------------------------------- #
# Auth endpoints
# --------------------------------------------------------------------------- #

# The trusted-device store lives in a file, NOT in the Django session: the
# base session expires after SESSION_COOKIE_AGE (4h) and is flushed on base
# logout, which silently re-prompted for a 2FA code on every connect even
# though Migratis trusts the device for a week. The file decouples the trust
# from the base app's login lifecycle. It holds only the `tfa_verified`
# cookie value (not a session), keyed by instance URL + account email.

def _trust_file() -> Path:
    d = _patches_dir(Path(settings.BASE_DIR))
    d.mkdir(exist_ok=True)
    return d / '.installer_trust.json'


def _load_trust_store() -> dict:
    try:
        return json.loads(_trust_file().read_text())
    except (OSError, ValueError):
        return {}


def _save_trust_store(store: dict):
    # Owner-only permissions from the moment of creation — the file holds the
    # 2FA-skip token for the Migratis connection.
    f  = _trust_file()
    fd = os.open(str(f), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as fh:
        fh.write(json.dumps(store, indent=2))
    try:
        os.chmod(f, 0o600)  # in case the file pre-existed with wider perms
    except OSError:
        pass
    _chown_to_owner(f, Path(settings.BASE_DIR))


def _trust_key(url, email):
    return f"{(url or '').rstrip('/')}|{(email or '').strip().lower()}"


def _store_tfa_cookie(url, email, session):
    """Persist the Migratis trusted-device cookie (`tfa_verified`) for this
    instance + account so future logins skip 2FA for up to a week — the
    installer's counterpart to the browser keeping the cookie. The expiry
    mirrors Migratis' max-age, so the trust survives disconnects and stale
    Migratis sessions but is not honoured forever."""
    value = session.cookies.get(MIGRATIS_TFA_COOKIE)
    if not value:
        return
    store = _load_trust_store()
    store[_trust_key(url, email)] = {
        'value':   value,
        'expires': (datetime.now(dt_timezone.utc)
                    + timedelta(days=MIGRATIS_TFA_TRUST_DAYS)).isoformat(),
    }
    _save_trust_store(store)


def _trusted_tfa_cookie(url, email):
    """Return the stored, non-expired trusted-device cookie value for this
    instance + account, or None. Drops the entry once it has expired so 2FA
    is asked again after a week."""
    store = _load_trust_store()
    key   = _trust_key(url, email)
    entry = store.get(key)
    if not entry:
        return None
    try:
        if datetime.fromisoformat(entry['expires']) <= datetime.now(dt_timezone.utc):
            store.pop(key, None)
            _save_trust_store(store)
            return None
    except (ValueError, KeyError, TypeError):
        return None
    return entry.get('value')


@router.post('/connect', auth=None)
def installer_connect(request):
    try:
        body = json.loads(request.body)
    except Exception:
        return _err('form', 'invalid-request')

    email    = (body.get('email') or '').strip()
    password = (body.get('password') or '').strip()
    url      = (body.get('url') or MIGRATIS_BACKEND_URL).rstrip('/')

    if not email or not password:
        return _err('form', 'missing-credentials')

    # Replay the stored trusted-device cookie so a remembered device skips 2FA
    # (the Migratis login logs in directly when `tfa_verified` is present).
    trusted = _trusted_tfa_cookie(url, email)
    login_cookies = {MIGRATIS_TFA_COOKIE: trusted} if trusted else None

    try:
        s    = http_requests.Session()
        resp = s.post(
            f'{url}/backend/api/user/login',
            data={'email': email, 'password': password},
            cookies=login_cookies,
            timeout=10,
        )
    except Exception:
        return JsonResponse({'detail': [{'url': ['connection-failed']}]}, status=503)

    if resp.status_code != 200:
        return JsonResponse({
            'detail': [{'credentials': ['invalid-credentials']}],
            '_debug': {'status': resp.status_code, 'body': resp.text[:500]},
        }, status=401)

    try:
        payload = resp.json()
    except Exception:
        payload = {}

    # The Migratis login enforces 2FA: when valid credentials are supplied
    # without a trusted-device cookie it returns 200 with {tfa_required: True}
    # (a code is emailed) and does NOT log in. Surface that so the frontend can
    # collect the code; remember the instance URL for the verify step.
    if payload.get('tfa_required'):
        request.session['migratis_url'] = url
        request.session.pop('migratis_cookies', None)
        request.session.modified = True
        return JsonResponse({'tfa_required': True, 'email': email})

    # A real login carries a user (and a session cookie). Anything else is not
    # an authenticated session — do not store empty cookies and claim success.
    if not payload.get('user'):
        return JsonResponse({'detail': [{'credentials': ['invalid-credentials']}]}, status=401)

    request.session['migratis_cookies'] = dict(s.cookies)
    request.session['migratis_url']     = url
    request.session.modified            = True

    return JsonResponse({'user': payload.get('user', {})})


@router.post('/tfa', auth=None)
def installer_tfa(request):
    """Complete the Migratis 2FA flow: verify the emailed code, then store the
    resulting authenticated session cookies so subsequent calls are connected."""
    try:
        body = json.loads(request.body)
    except Exception:
        return _err('form', 'invalid-request')

    email = (body.get('email') or '').strip()
    code  = (body.get('code') or '').strip()
    url   = (body.get('url') or request.session.get('migratis_url') or MIGRATIS_BACKEND_URL).rstrip('/')

    if not email or not code:
        return JsonResponse({'detail': [{'code': ['tfa-code-required']}]}, status=400)

    try:
        s    = http_requests.Session()
        resp = s.post(
            f'{url}/backend/api/user/tfa/verify',
            data={'email': email, 'code': code, 'remember_device': 'true'},
            timeout=10,
        )
    except Exception:
        return JsonResponse({'detail': [{'url': ['connection-failed']}]}, status=503)

    if resp.status_code != 200:
        # Propagate the remote's error key (tfa-code-invalid / -expired / -max-attempts).
        try:
            return JsonResponse(resp.json(), status=resp.status_code)
        except Exception:
            return JsonResponse({'detail': [{'code': ['tfa-code-invalid']}]}, status=400)

    try:
        payload = resp.json()
    except Exception:
        payload = {}

    if not payload.get('user'):
        return JsonResponse({'detail': [{'code': ['tfa-code-invalid']}]}, status=400)

    request.session['migratis_cookies'] = dict(s.cookies)
    request.session['migratis_url']     = url
    request.session.modified            = True

    # Remember this device so the next connect skips 2FA for a week.
    _store_tfa_cookie(url, email, s)

    return JsonResponse({'user': payload.get('user', {})})


@router.delete('/connect', auth=None)
def installer_disconnect(request):
    request.session.pop('migratis_cookies', None)
    request.session.pop('migratis_url', None)
    return JsonResponse({'success': True})


@router.get('/session', auth=None)
def installer_session(request):
    return JsonResponse({'connected': bool(request.session.get('migratis_cookies'))})


# --------------------------------------------------------------------------- #
# App listing
# --------------------------------------------------------------------------- #

@router.get('/apps', auth=None)
def installer_list_apps(request):
    s, url = _session(request)
    if s is None:
        return JsonResponse({'detail': [{'session': ['not-connected']}]}, status=401)

    try:
        resp = s.get(f'{url}/backend/api/generator/application/list?limit=100&offset=0', timeout=10)
    except Exception:
        return JsonResponse({'detail': [{'session': ['connection-failed']}]}, status=503)

    # The stored Migratis session went stale (logged out / expired upstream).
    # Forget it so the UI returns to the login form rather than looping on errors.
    if resp.status_code in (401, 403):
        _clear_migratis_session(request)
        return _session_expired_response()
    if resp.status_code != 200:
        return _session_expired_response()

    # Annotate each app with its derived module name and whether it is already
    # installed, so the UI can present installed apps as installed rather than
    # offering to install them again. The remote schema does not expose `module`.
    # Installed apps also get upgrade info: the remote `generation` counter vs
    # the schema_version recorded in the local manifest at install time.
    backend_root = Path(settings.BASE_DIR)
    installed = set(_get_installed_modules(backend_root))
    apps = []
    for a in resp.json().get('items', []):
        if a.get('status') != 'generated':
            continue
        module = _module_name(a.get('name'))
        a['module'] = module
        a['installed'] = module in installed
        if a['installed']:
            manifest = _read_installed_manifest(backend_root, module) or {}
            installed_version = manifest.get('schema_version')
            remote_version    = a.get('generation') or 0
            # Apps installed before schema versioning have no recorded version;
            # they are treated as v1 (the first versioned generation freezes
            # the existing 0001_initial as its baseline) and flagged legacy so
            # the UI can warn that pre-versioning spec changes are not covered.
            a['installed_schema_version'] = installed_version
            a['upgrade_legacy']     = installed_version is None
            a['upgrade_available']  = remote_version > (installed_version or 1)
        apps.append(a)
    return JsonResponse({'apps': apps})


# --------------------------------------------------------------------------- #
# Installation
# --------------------------------------------------------------------------- #

@router.post('/install/{app_id}', auth=None)
def installer_install(request, app_id: int):
    s, url = _session(request)
    if s is None:
        return JsonResponse({'detail': [{'session': ['not-connected']}]}, status=401)

    # Optional install-time config collected by the wizard: {admin, email, stripe}.
    try:
        config = json.loads(request.body) if request.body else {}
    except Exception:
        config = {}

    try:
        resp = s.get(f'{url}/backend/api/generator/application/{app_id}/download', timeout=60)
    except Exception:
        return JsonResponse({'detail': [{'download': ['download-failed']}]}, status=503)

    if resp.status_code in (401, 403):
        _clear_migratis_session(request)
        return _session_expired_response()
    if resp.status_code != 200:
        return JsonResponse({'detail': [{'download': ['download-failed']}]}, status=resp.status_code)

    try:
        result = _apply_package(resp.content, config=config)
    except Exception as exc:
        return JsonResponse({'detail': [{'install': [str(exc)]}]}, status=500)

    return JsonResponse(result)


@router.get('/frontend-zip/{app_id}', auth=None)
def installer_frontend_zip(request, app_id: int):
    s, url = _session(request)
    if s is None:
        return JsonResponse({'detail': [{'session': ['not-connected']}]}, status=401)

    try:
        resp = s.get(f'{url}/backend/api/generator/application/{app_id}/download', timeout=60)
    except Exception:
        return JsonResponse({'detail': [{'download': ['download-failed']}]}, status=503)

    if resp.status_code in (401, 403):
        _clear_migratis_session(request)
        return _session_expired_response()
    if resp.status_code != 200:
        return JsonResponse({'detail': [{'download': ['download-failed']}]}, status=resp.status_code)

    with zipfile.ZipFile(io.BytesIO(resp.content), 'r') as zf:
        manifest = json.loads(zf.read('manifest.json'))
        module   = manifest['module']

        out_buf = io.BytesIO()
        with zipfile.ZipFile(out_buf, 'w', zipfile.ZIP_DEFLATED) as out:
            for name in zf.namelist():
                if name.startswith('frontend/src/'):
                    out.writestr(name[len('frontend/'):], zf.read(name))
            if 'frontend/app_additions.json' in zf.namelist():
                raw = json.loads(zf.read('frontend/app_additions.json'))
                out.writestr('app_additions.json', json.dumps(raw, indent=2))
                out.writestr('INSTALL.md', _build_install_instructions(module, raw))

    out_buf.seek(0)
    response = HttpResponse(out_buf.read(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{module}_frontend.zip"'
    return response


# --------------------------------------------------------------------------- #
# Installed modules listing
# --------------------------------------------------------------------------- #

@router.get('/installed', auth=None)
def installer_list_installed(request):
    backend_root = Path(settings.BASE_DIR)
    try:
        modules = _get_installed_modules(backend_root)
    except Exception as exc:
        return JsonResponse({'detail': [{'installed': [str(exc)]}]}, status=500)
    return JsonResponse({'modules': modules})


# --------------------------------------------------------------------------- #
# Uninstallation
# --------------------------------------------------------------------------- #

@router.post('/uninstall/{module}', auth=None)
def installer_uninstall(request, module: str):
    backend_root = Path(settings.BASE_DIR)

    if module not in _get_installed_modules(backend_root):
        return JsonResponse({'detail': [{'module': ['not-installed']}]}, status=404)

    try:
        result = _remove_module(module, backend_root)
    except Exception as exc:
        return JsonResponse({'detail': [{'uninstall': [str(exc)]}]}, status=500)

    return JsonResponse(result)


# --------------------------------------------------------------------------- #
# Upgrade
# --------------------------------------------------------------------------- #
#
# An installed module is upgraded in place, keeping its data:
#   preview — download the package, read upgrade.json (the per-version
#             operation lists Migratis records at each generation), pick the
#             versions newer than the locally installed schema_version, and
#             annotate destructive/lossy operations with live row counts so
#             the user confirms exactly what the upgrade will touch.
#   apply   — backup (dumpdata + code snapshot), write ONLY the new migration
#             files (not watched by the autoreloader), run `migrate <module>`
#             synchronously, and only on success write the rest of the package
#             (watched backend sources last, mirroring _apply_package's
#             ordering). On migrate failure the DB is unwound to the previously
#             applied migration and the new migration files are removed, so
#             the old version keeps running untouched.
#
# Seeds are intentionally NOT re-run on upgrade (user-edited data must
# survive); the response carries the command to refresh translations manually.

def _read_installed_manifest(backend_root: Path, module: str):
    f = _patches_dir(backend_root) / f'{module}_manifest.json'
    try:
        return json.loads(f.read_text())
    except (OSError, ValueError):
        return None


def _download_package(request, s, url, app_id):
    """Download a generated package ZIP. Returns (zip_bytes, error_response)."""
    try:
        resp = s.get(f'{url}/backend/api/generator/application/{app_id}/download', timeout=60)
    except Exception:
        return None, JsonResponse({'detail': [{'download': ['download-failed']}]}, status=503)
    if resp.status_code in (401, 403):
        _clear_migratis_session(request)
        return None, _session_expired_response()
    if resp.status_code != 200:
        return None, JsonResponse({'detail': [{'download': ['download-failed']}]}, status=resp.status_code)
    return resp.content, None


def _op_severity(op):
    if op.get('destructive') or op.get('op') in ('remove_field', 'delete_model'):
        return 'destructive'
    if op.get('lossy'):
        return 'lossy'
    return 'safe'


def _probe_rows(module, op):
    """Best-effort live row count for a destructive/lossy operation, shown on
    the confirmation screen ('column X dropped — 1240 rows hold a value').
    ORM-based — the module is installed, so its (pre-upgrade) models are in
    the app registry, and the queries work on any backend (SQLite in local
    bases, Postgres in production). Returns None when the count cannot be
    computed (e.g. ops on a model renamed in the same upgrade)."""
    from django.apps import apps as django_apps
    from django.db.models.functions import Length

    model_name = op.get('model')
    if not model_name:
        return None
    try:
        model = django_apps.get_model(module, model_name)
    except Exception:
        return None

    name = op.get('name')
    try:
        if op.get('op') == 'delete_model':
            return model.objects.count()
        if not name:
            return None
        if op.get('field') == 'ManyToManyField':
            return None  # the data lives in a join table, not a column
        non_null = model.objects.exclude(**{f'{name}__isnull': True})
        if op.get('op') == 'remove_field':
            return non_null.count()
        probe = op.get('probe') or {}
        kind  = probe.get('kind')
        if kind == 'non_numeric':
            return non_null.exclude(
                **{f'{name}__regex': probe.get('pattern', r'^-?[0-9]+$')}
            ).count()
        if kind == 'too_long':
            return (non_null.annotate(_probe_len=Length(name))
                    .filter(_probe_len__gt=probe.get('max_length', 255)).count())
        if kind == 'non_boolean':
            return non_null.exclude(
                **{f'{name}__iregex': r'^(true|false|t|f|0|1|yes|no)$'}
            ).count()
        if kind == 'null_required':
            return model.objects.filter(**{f'{name}__isnull': True}).count()
        if kind == 'time_truncated':
            return non_null.exclude(**{f'{name}__time': '00:00:00'}).count()
        return non_null.count()
    except Exception:
        return None


def _build_upgrade_preview(zip_bytes: bytes, backend_root: Path) -> dict:
    with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
        manifest = json.loads(zf.read('manifest.json'))
        upgrade  = (json.loads(zf.read('upgrade.json'))
                    if 'upgrade.json' in zf.namelist() else {})
    module = manifest['module']
    if module not in _get_installed_modules(backend_root):
        raise ValueError('not-installed')

    local             = _read_installed_manifest(backend_root, module) or {}
    installed_version = local.get('schema_version')
    # Pre-versioning installs have no recorded version: the first versioned
    # generation froze the already-applied 0001_initial as its v1 baseline,
    # so they are treated as v1 (flagged legacy for the UI caveat).
    effective = installed_version or 1
    target    = manifest.get('schema_version') or upgrade.get('schema_version') or 1

    changes = []
    requires_confirmation = False
    for v in (upgrade.get('versions') or []):
        if not (effective < v.get('version', 0) <= target):
            continue
        for op in (v.get('operations') or []):
            severity = _op_severity(op)
            entry = {
                'version':  v['version'],
                'op':       op.get('op'),
                'model':    op.get('model') or op.get('new_model') or op.get('old_model'),
                'name':     op.get('name') or op.get('new_name'),
                'old_name': op.get('old_name'),
                'from':     (op.get('from_decl') or {}).get('field'),
                'to':       (op.get('to_decl') or {}).get('field'),
                'severity': severity,
                'rows':     None,
            }
            if severity != 'safe':
                entry['rows'] = _probe_rows(module, op)
                requires_confirmation = True
            changes.append(entry)

    return {
        'module':                module,
        'installed_version':     effective,
        'target_version':        target,
        'legacy':                installed_version is None,
        'up_to_date':            target <= effective,
        'changes':               changes,
        'requires_confirmation': requires_confirmation,
    }


def _last_applied_migration(module: str):
    from django.db import connection
    with connection.cursor() as cur:
        cur.execute(
            'SELECT name FROM django_migrations WHERE app = %s ORDER BY id DESC LIMIT 1',
            [module],
        )
        row = cur.fetchone()
    return row[0] if row else None


def _reconcile_schema_drift(module: str) -> list:
    """
    Add columns the installed models declare but the tables lack.

    Apps installed before schema versioning froze their AI-written
    0001_initial; any spec change made between that install and the first
    versioned generation has no migration, so models.py can reference
    columns that were never created. That drift breaks every ORM read —
    including the dumpdata backup that gates an upgrade.

    Strictly additive: missing columns are added (NOT NULL ones get a
    type-appropriate backfill default), nothing is altered or dropped, and
    missing TABLES are left to the migration chain. Returns the list of
    columns added ('table.column').
    """
    import datetime as _dt
    from django.apps import apps as django_apps
    from django.db import connection
    from django.utils import timezone as _tz

    _BACKFILL = {
        'CharField': '', 'TextField': '', 'EmailField': '', 'URLField': '',
        'SlugField': '',
        'IntegerField': 0, 'BigIntegerField': 0, 'SmallIntegerField': 0,
        'PositiveIntegerField': 0, 'PositiveSmallIntegerField': 0,
        'DecimalField': 0, 'FloatField': 0.0, 'BooleanField': False,
        'DateTimeField': _tz.now, 'DateField': _dt.date.today,
        'JSONField': dict,
    }

    try:
        app_config = django_apps.get_app_config(module)
    except LookupError:
        return []

    def _columns(table):
        with connection.cursor() as cur:
            return {c.name for c in connection.introspection.get_table_description(cur, table)}

    added = []
    existing_tables = set(connection.introspection.table_names())
    for model in app_config.get_models():
        table = model._meta.db_table
        if table not in existing_tables:
            continue
        # Add one field at a time and RECOMPUTE what's missing after each:
        # on SQLite a NOT NULL add goes through a full table remake built
        # from the model, which heals every missing column of that table in
        # one shot — blindly looping over the original list would then try
        # to re-add columns that already exist.
        while True:
            cols = _columns(table)
            missing = [f for f in model._meta.local_fields if f.column not in cols]
            if not missing:
                break
            field = missing[0]
            new_field = field.clone()
            # clone() returns an unbound field — rebind so the schema
            # editor sees column/attname/concrete.
            new_field.set_attributes_from_name(field.name)
            new_field.model = model
            if not new_field.null and not new_field.has_default():
                internal = new_field.get_internal_type()
                if internal in _BACKFILL:
                    new_field.default = _BACKFILL[internal]
                else:
                    new_field.null = True
            with connection.schema_editor() as editor:
                editor.add_field(model, new_field)
            added += sorted(f'{table}.{c}' for c in (_columns(table) - cols))
    return added


def _apply_upgrade(zip_bytes: bytes, backend_root: Path, confirm: bool) -> dict:
    frontend_root = Path(getattr(settings, 'FRONTEND_SRC_DIR', '/frontend/src'))
    patches_dir   = _patches_dir(backend_root)

    preview = _build_upgrade_preview(zip_bytes, backend_root)
    module  = preview['module']
    if preview['up_to_date']:
        raise ValueError('already-up-to-date')
    if preview['requires_confirmation'] and not confirm:
        return {'needs_confirmation': True, 'preview': preview}

    with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
        names    = zf.namelist()
        manifest = json.loads(zf.read('manifest.json'))

        # ── Pre-flight: never apply a package whose Python doesn't compile ──
        invalid = _validate_package_python(zf, module)
        if invalid:
            raise RuntimeError('package-invalid: ' + '; '.join(invalid))

        # ── 0. Repair legacy schema drift (additive only) ──────────────────
        # Pre-versioning installs may have columns declared in models.py that
        # no migration ever created; the ORM-based dumpdata below would fail
        # on them. Add what's missing so the backup (and the app) work.
        repaired_columns = _reconcile_schema_drift(module)

        # ── 1. Backup: data dump + code snapshot ───────────────────────────
        ts = datetime.now(dt_timezone.utc).strftime('%Y%m%d_%H%M%S')
        backup_dir = backend_root / 'backups' / f"{module}_v{preview['installed_version']}_{ts}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        dump = subprocess.run(
            ['python', 'manage.py', 'dumpdata', module, '--indent', '2',
             '-o', str(backup_dir / 'data.json')],
            cwd=str(backend_root), capture_output=True, text=True, timeout=300,
        )
        if dump.returncode != 0:
            # No backup → no upgrade. The whole point is never to risk the data.
            shutil.rmtree(backup_dir, ignore_errors=True)
            raise RuntimeError(f"backup-failed: {(dump.stderr or dump.stdout)[-500:]}")
        if (backend_root / module).exists():
            shutil.copytree(backend_root / module, backup_dir / 'backend')
        if (frontend_root / module).exists():
            shutil.copytree(frontend_root / module, backup_dir / 'frontend')
        for fname in (f'{module}.py', f'{module}_manifest.json', f'{module}_additions.json'):
            src = patches_dir / fname
            if src.exists():
                shutil.copy2(src, backup_dir / fname)

        # ── 2. Write ONLY the new migration files ──────────────────────────
        # Migration modules already on disk are identical (the chain is
        # append-only) and skipping them avoids touching files the
        # autoreloader watches before migrate has run.
        last_applied   = _last_applied_migration(module)
        new_migrations = []
        mig_prefix     = f'backend/{module}/migrations/'
        for name in names:
            if not name.startswith(mig_prefix) or name.endswith('/'):
                continue
            content = zf.read(name)
            if name.endswith('.py'):
                content = _fix_backend_py(content, module, name)
            dest = backend_root / name[len('backend/'):]
            if dest.exists() and dest.read_bytes() == content:
                continue
            existed = dest.exists()
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(content)
            if not existed:
                new_migrations.append(dest)
        pycache = backend_root / module / 'migrations' / '__pycache__'
        if pycache.exists():
            shutil.rmtree(pycache, ignore_errors=True)

        # ── 3. Migrate synchronously (the app is already installed, so the
        #       subprocess sees it in INSTALLED_APPS) ───────────────────────
        migrate = subprocess.run(
            ['python', 'manage.py', 'migrate', module],
            cwd=str(backend_root), capture_output=True, text=True, timeout=300,
        )
        if migrate.returncode != 0:
            # ── Auto-rollback: unwind the DB, drop the new migration files ──
            rolled_back = False
            if last_applied:
                undo = subprocess.run(
                    ['python', 'manage.py', 'migrate', module, last_applied],
                    cwd=str(backend_root), capture_output=True, text=True, timeout=300,
                )
                rolled_back = undo.returncode == 0
            for f in new_migrations:
                try:
                    f.unlink()
                except OSError:
                    pass
            return {
                'success':        False,
                'module':         module,
                'from_version':   preview['installed_version'],
                'to_version':     preview['target_version'],
                'repaired_columns': repaired_columns,
                'migrate_ok':     False,
                'migrate_output': (migrate.stdout or migrate.stderr)[-2000:],
                'rolled_back':    rolled_back,
                'backup_path':    str(backup_dir.relative_to(backend_root)),
            }

        # ── 4. Frontend module — mirror the package exactly (drop files of
        #       removed entities), then metadata + registry ─────────────────
        frontend_ok = frontend_root.exists()
        if frontend_ok:
            module_dir = frontend_root / module
            if module_dir.exists():
                shutil.rmtree(module_dir)
            for name in names:
                if not name.startswith('frontend/src/'):
                    continue
                rel = name[len('frontend/src/'):]
                if not rel or rel.endswith('/'):
                    continue
                dest = frontend_root / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(zf.read(name))

        manifest_file = patches_dir / f'{module}_manifest.json'
        manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
        if 'frontend/app_additions.json' in names:
            additions = json.loads(zf.read('frontend/app_additions.json'))
            (patches_dir / f'{module}_additions.json').write_text(
                json.dumps(additions, indent=2, ensure_ascii=False)
            )

        # The settings patch follows the new package (modules_needed may have
        # changed); settings_patches/*.py are exec'd, not imported, so writing
        # them does not trigger the autoreloader.
        if 'backend/settings_patch.py' in names:
            settings_txt = (backend_root / 'migratis' / 'settings.py').read_text()
            patch_src    = zf.read('backend/settings_patch.py').decode('utf-8')
            filtered = '\n'.join(
                line for line in patch_src.splitlines()
                if not (line.startswith('INSTALLED_APPS +=') and line in settings_txt)
            )
            (patches_dir / f'{module}.py').write_text(filtered)

        _write_language_patch(backend_root)
        if frontend_ok:
            _sync_frontend_flags(backend_root, frontend_root)
            _sync_frontend_language(backend_root, frontend_root)
            _rebuild_registry(backend_root, frontend_root)

        # ── 5. Backend source files LAST — they are watched by the
        #       autoreloader, so the dev reload fires only after everything
        #       above has completed (mirrors _apply_package's ordering) ─────
        for name in names:
            if not name.startswith('backend/'):
                continue
            rel = name[len('backend/'):]
            if (not rel or rel == 'settings_patch.py'
                    or name.startswith(mig_prefix) or name.endswith('/')):
                continue
            content = zf.read(name)
            if name.endswith('.py'):
                content = _fix_backend_py(content, module, name)
            dest = backend_root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(content)

        # ── 6. Ownership fixes ──────────────────────────────────────────────
        uid, gid = _volume_owner(backend_root)
        if uid != 0:
            _chown_tree(backend_root / module, uid, gid)
            _chown_tree(patches_dir, uid, gid)
            _chown_tree(backup_dir, uid, gid)
            if frontend_ok:
                _chown_tree(frontend_root / module, uid, gid)
                registry = frontend_root / 'module_registry.js'
                if registry.exists():
                    try:
                        os.chown(registry, uid, gid)
                    except OSError:
                        pass

        _sync_framework_routers(backend_root)

    return {
        'success':              True,
        'module':               module,
        'from_version':         preview['installed_version'],
        'to_version':           preview['target_version'],
        'legacy':               preview['legacy'],
        'repaired_columns':     repaired_columns,
        'migrate_ok':           True,
        'migrate_output':       (migrate.stdout or migrate.stderr)[-2000:],
        'frontend_ok':          frontend_ok,
        'backup_path':          str(backup_dir.relative_to(backend_root)),
        # Seeds are skipped on purpose; new translation keys arrive only when
        # the user re-runs the module's seed command.
        'seed_skipped':         True,
        'translations_command': f'docker exec backend-base-api-1 python /backend/manage.py seed_{module}',
        'restart_required':     not _backend_autoreloads(),
    }


@router.post('/upgrade/{app_id}/preview', auth=None)
def installer_upgrade_preview(request, app_id: int):
    s, url = _session(request)
    if s is None:
        return _session_expired_response()
    zip_bytes, err = _download_package(request, s, url, app_id)
    if err:
        return err
    try:
        preview = _build_upgrade_preview(zip_bytes, Path(settings.BASE_DIR))
    except ValueError as exc:
        return JsonResponse({'detail': [{'upgrade': [str(exc)]}]}, status=400)
    except Exception as exc:
        return JsonResponse({'detail': [{'upgrade': [str(exc)]}]}, status=500)
    return JsonResponse(preview)


@router.post('/upgrade/{app_id}', auth=None)
def installer_upgrade(request, app_id: int):
    s, url = _session(request)
    if s is None:
        return _session_expired_response()
    try:
        body = json.loads(request.body) if request.body else {}
    except Exception:
        body = {}
    zip_bytes, err = _download_package(request, s, url, app_id)
    if err:
        return err
    try:
        result = _apply_upgrade(zip_bytes, Path(settings.BASE_DIR),
                                confirm=bool(body.get('confirm')))
    except ValueError as exc:
        return JsonResponse({'detail': [{'upgrade': [str(exc)]}]}, status=400)
    except Exception as exc:
        return JsonResponse({'detail': [{'upgrade': [str(exc)]}]}, status=500)
    if result.get('needs_confirmation'):
        return JsonResponse(result, status=409)
    return JsonResponse(result)


# --------------------------------------------------------------------------- #
# Package application logic
# --------------------------------------------------------------------------- #

def _apply_package(zip_bytes: bytes, config: dict = None) -> dict:
    """
    Extract a generated package ZIP and apply it to this project.

    Backend:
      1. Write backend app source files.
      2. Activate required framework routers in api/views.py (uncomment).
      3. Write settings_patches/<module>.py with module-only INSTALLED_APPS line.
      4. Write settings_patches/<module>_additions.json for registry rebuild.

    Frontend:
      5. Write frontend source files.
      6. Rebuild module_registry.js.

    DB:
      7. migrate --run-syncdb
      8. seed_<module>
    """
    backend_root  = Path(settings.BASE_DIR)
    frontend_root = Path(getattr(settings, 'FRONTEND_SRC_DIR', '/frontend/src'))
    patches_dir   = _patches_dir(backend_root)
    patches_dir.mkdir(exist_ok=True)
    installed_files = []

    with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
        names    = zf.namelist()
        manifest = json.loads(zf.read('manifest.json'))
        module   = manifest['module']

        # ── Pre-flight: never apply a package whose Python doesn't compile ──
        invalid = _validate_package_python(zf, module)
        if invalid:
            raise RuntimeError('package-invalid: ' + '; '.join(invalid))

        # ── 1. Backend source files ────────────────────────────────────────
        for name in names:
            if not name.startswith('backend/'):
                continue
            rel = name[len('backend/'):]
            if rel in ('', 'settings_patch.py'):
                continue
            dest = backend_root / rel
            if name.endswith('/'):
                dest.mkdir(parents=True, exist_ok=True)
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            content = zf.read(name)
            if name.endswith('.py'):
                content = _fix_backend_py(content, module, name)
            dest.write_bytes(content)
            installed_files.append(f'backend/{rel}')

        # IMPORTANT — ordering vs. the StatReloader.
        # Writing api/views.py (an imported module) triggers Django's autoreloader,
        # which restarts the process ~1 s later and kills this request handler.
        # The new app dir (step 1) and settings_patches/*.py are NOT watched (not
        # imported / exec'd), so they don't trigger it. Therefore every write that
        # MUST complete — settings patch, .env/config, language, feature flags,
        # the slow frontend copy, and the pending marker — happens first, and the
        # api/views.py router activation is done LAST so the reload fires only
        # after the response is composed.

        # ── 2. Settings patch file (idempotent) ────────────────────────────
        patch_file = patches_dir / f'{module}.py'
        if not patch_file.exists():
            # Only write the module's own INSTALLED_APPS line — filter out
            # framework lines that are already present in settings.py.
            settings_txt = (backend_root / 'migratis' / 'settings.py').read_text()
            patch_src    = zf.read('backend/settings_patch.py').decode('utf-8')
            filtered = '\n'.join(
                line for line in patch_src.splitlines()
                if not (line.startswith('INSTALLED_APPS +=') and line in settings_txt)
            )
            patch_file.write_text(filtered)

        # Persist the manifest so reconciliation can recompute the language set
        # and module metadata after any later install/uninstall.
        manifest_file = patches_dir / f'{module}_manifest.json'
        manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))

        # ── 3. Install-time config (.env + frontend Stripe key) ────────────
        # Fast and critical — do it before the slow frontend copy. Returns admin
        # creds to defer (user tables don't exist until migrate runs).
        admin = _apply_install_config(backend_root, frontend_root, config)

        # ── 4. Default language (backend patch) ────────────────────────────
        _write_language_patch(backend_root)

        # ── 5. Frontend additions metadata ────────────────────────────────
        additions = {}
        if 'frontend/app_additions.json' in names:
            additions = json.loads(zf.read('frontend/app_additions.json'))
            additions_file = patches_dir / f'{module}_additions.json'
            additions_file.write_text(json.dumps(additions, indent=2, ensure_ascii=False))

        # ── 6. Feature flags + frontend language (fast, before the copy) ───
        # Turn on USER/SUBSCRIPTION/SUPPORT/COOKIE so module routes/links render,
        # and point the frontend default language at the app's main_language.
        frontend_ok = frontend_root.exists()
        if frontend_ok:
            _sync_frontend_flags(backend_root, frontend_root)
            _sync_frontend_language(backend_root, frontend_root)

        # ── 7. Defer migrate + seed (+ admin) to InstallerConfig.ready() ───
        # Written before the slow copy so it survives even if a stray reload
        # interrupts the request. The user app tables don't exist until the
        # deferred migrate runs, so admin creation is deferred alongside it.
        pending = patches_dir / '_pending_install.json'
        pending_payload = {'module': module}
        if admin:
            # Stash admin creds for deferred create_superuser (file removed after
            # the deferred run succeeds). Local-container installer only.
            pending_payload['admin'] = admin
        pending.write_text(json.dumps(pending_payload))

        # ── 8. Frontend source files + registry (the slow part) ────────────
        if frontend_ok:
            for name in names:
                if not name.startswith('frontend/src/'):
                    continue
                rel = name[len('frontend/src/'):]
                if not rel or rel.endswith('/'):
                    continue
                dest = frontend_root / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(zf.read(name))
                installed_files.append(f'frontend/src/{rel}')
            _rebuild_registry(backend_root, frontend_root)

        # ── 9. Fix ownership — chown written files back to the volume owner ─
        uid, gid = _volume_owner(backend_root)
        if uid != 0:  # only needed when container runs as root
            _chown_tree(backend_root / module, uid, gid)
            _chown_tree(patches_dir, uid, gid)
            if frontend_ok:
                _chown_tree(frontend_root / module, uid, gid)
                registry = frontend_root / 'module_registry.js'
                if registry.exists():
                    try:
                        os.chown(registry, uid, gid)
                    except OSError:
                        pass

        # ── 10. Framework router activation — LAST (triggers the reload) ───
        # Reconcile api/views.py against the apps now in INSTALLED_APPS. Done last
        # so the autoreload restart happens only after every critical write above
        # has completed and the response is ready to return.
        _sync_framework_routers(backend_root)

    return {
        'success':          True,
        'module':           module,
        'installed_files':  installed_files,
        'manifest':         manifest,
        'frontend_ok':      frontend_ok,
        'migrate_ok':       None,
        'migrate_output':   'Deferred — will run automatically on backend restart.',
        'seed_ok':          None,
        'seed_output':      'Deferred — will run automatically on backend restart.',
        'migrate_deferred': True,
        # Dev autoreloader restarts the worker (and runs the deferred migrate) on
        # its own when api/views.py is rewritten; only production needs a manual one.
        'restart_required': not _backend_autoreloads(),
    }


def _installed_framework_apps(backend_root: Path) -> set:
    """
    Return the set of framework router keys whose Django app is currently active
    in INSTALLED_APPS — scanning base settings.py plus every remaining
    settings_patches/<module>.py. Commented-out lines are ignored, so a framework
    app counts as active only if some currently-installed module still requires it.
    """
    texts = []
    settings_file = backend_root / 'migratis' / 'settings.py'
    if settings_file.exists():
        texts.append(settings_file.read_text())
    patches_dir = _patches_dir(backend_root)
    if patches_dir.exists():
        for patch in patches_dir.glob('*.py'):
            try:
                texts.append(patch.read_text())
            except OSError:
                pass

    active = set()
    for key, _rname, _rmod, _rpath in _FRAMEWORK_ROUTERS:
        token = f'migratis.{key}.apps'
        for txt in texts:
            if any(token in line and not line.strip().startswith('#')
                   for line in txt.splitlines()):
                active.add(key)
                break
    return active


def _sync_framework_routers(backend_root: Path) -> bool:
    """
    Reconcile the framework router imports/mounts in api/views.py with the set of
    framework apps still present in INSTALLED_APPS. Uncomment routers whose app is
    active; comment routers whose app is no longer installed. Idempotent.

    This is the uninstall counterpart to step 2 of _apply_package: install
    uncomments routers a module needs, and this re-comments them once no remaining
    module needs them — preventing api/views.py from importing models for an app
    that is no longer in INSTALLED_APPS.
    """
    api_views = backend_root / 'migratis' / 'api' / 'views.py'
    if not api_views.exists():
        return False

    txt    = api_views.read_text()
    active = _installed_framework_apps(backend_root)
    changed = False
    for key, rname, rmod, rpath in _FRAMEWORK_ROUTERS:
        for stmt in (f'from {rmod} import router as {rname}',
                     f'api.add_router("{rpath}", {rname})'):
            commented = f'# {stmt}'
            if key in active:
                if commented in txt:
                    txt = txt.replace(commented, stmt)
                    changed = True
            else:
                # Only comment a statement that is currently active (the commented
                # form absent guards against double-commenting and against the
                # aligned always-on i18n/cookie mounts that use different spacing).
                if commented not in txt and stmt in txt:
                    txt = txt.replace(stmt, commented)
                    changed = True

    if changed:
        api_views.write_text(txt)
        _chown_to_owner(api_views, backend_root)
    return changed


# --------------------------------------------------------------------------- #
# Frontend feature flags + language reconciliation
# --------------------------------------------------------------------------- #

# Frontend feature flag (frontend/src/settings.js) → framework app key. Toggled
# to match the apps currently in INSTALLED_APPS so module routes/links light up
# (without this, /register and friends stay gated off and render blank).
_FRONTEND_FLAGS = [
    ('USER',         'user'),
    ('SUBSCRIPTION', 'subscription'),
    ('SUPPORT',      'support'),
    ('COOKIE',       'cookie'),
]

_LANG_NAMES = {
    'en': 'English', 'fr': 'French', 'es': 'Spanish', 'ro': 'Romanian',
    'pt': 'Portuguese', 'de': 'German', 'it': 'Italian', 'nl': 'Dutch',
    'zh': 'Chinese',
}


def _chown_to_owner(path: Path, backend_root: Path):
    """Best-effort chown a single written file back to the volume owner so files
    created while the container runs as root stay editable by the host user."""
    uid, gid = _volume_owner(backend_root)
    if uid != 0:
        try:
            os.chown(path, uid, gid)
        except OSError:
            pass


def _sync_frontend_flags(backend_root: Path, frontend_root: Path) -> bool:
    """
    Reconcile the feature flags in frontend/src/settings.js with the framework
    apps currently in INSTALLED_APPS. Mirrors _sync_framework_routers: install
    turns a flag on, uninstall turns it back off once no module needs it. Without
    this the user/subscription/support/cookie routes in App.js stay gated off
    (e.g. /register renders blank). Idempotent.
    """
    settings_js = frontend_root / 'settings.js'
    if not settings_js.exists():
        return False

    txt     = settings_js.read_text()
    active  = _installed_framework_apps(backend_root)
    changed = False
    for flag, key in _FRONTEND_FLAGS:
        desired = 'true' if key in active else 'false'
        pattern = re.compile(rf'(export const {flag}\s*=\s*)(?:true|false)(\s*;)')
        new_txt = pattern.sub(rf'\g<1>{desired}\g<2>', txt)
        if new_txt != txt:
            txt = new_txt
            changed = True

    if changed:
        settings_js.write_text(txt)
        _chown_to_owner(settings_js, backend_root)
    return changed


def _installed_manifests(backend_root: Path) -> list:
    """Return manifest dicts for every installed module, ordered oldest→newest by
    file mtime so the most-recently-installed app wins for the primary language."""
    patches_dir = _patches_dir(backend_root)
    out = []
    if patches_dir.exists():
        for mf in patches_dir.glob('*_manifest.json'):
            try:
                out.append((mf.stat().st_mtime, json.loads(mf.read_text())))
            except (OSError, ValueError):
                pass
    out.sort(key=lambda t: t[0])
    return [m for _mtime, m in out]


def _language_config(backend_root: Path):
    """Compute (primary_language, [codes]) from installed manifests. primary =
    most-recently-installed app's main_language; codes = union of every app's
    main_language ∪ languages. Returns (None, []) when no app is installed."""
    manifests = _installed_manifests(backend_root)
    if not manifests:
        return None, []
    codes = set()
    primary = None
    for m in manifests:
        main = m.get('main_language') or 'en'
        codes.add(main)
        codes.update(m.get('languages') or [])
        primary = main  # newest wins (manifests are oldest→newest)
    return primary, sorted(codes)


def _write_language_patch(backend_root: Path) -> None:
    """Write settings_patches/zzz_language.py so backend LANGUAGE_CODE/LANGUAGES
    follow the installed app's main_language. Named to sort last among patches so
    it wins over the base settings.py default and any module patch. Removed when
    no app remains."""
    patch = _patches_dir(backend_root) / 'zzz_language.py'
    primary, codes = _language_config(backend_root)
    if not primary:
        if patch.exists():
            patch.unlink()
        return
    langs = ', '.join(f"('{c}', '{_LANG_NAMES.get(c, c.upper())}')" for c in codes)
    patch.write_text(
        "# ── language ── managed by the installer; follows the installed app ──\n"
        f"LANGUAGE_CODE = '{primary}'\n"
        f"LANGUAGES = [{langs}]\n"
    )
    _chown_to_owner(patch, backend_root)


def _sync_frontend_language(backend_root: Path, frontend_root: Path) -> bool:
    """Patch frontend/src/i18n.js fallbackLng + supportedLngs to match the
    installed app's languages (reverts to 'en' when none). The default language
    becomes the app's main_language; with the i18n module its chosen languages
    become selectable. Idempotent."""
    i18n_js = frontend_root / 'i18n.js'
    if not i18n_js.exists():
        return False
    primary, codes = _language_config(backend_root)
    if not primary:
        primary, codes = 'en', ['en']
    supported = '[' + ', '.join(f"'{c}'" for c in codes) + ']'

    txt = i18n_js.read_text()
    new = re.sub(r"fallbackLng:\s*'[^']*'", f"fallbackLng: '{primary}'", txt)
    new = re.sub(r"supportedLngs:\s*\[[^\]]*\]", f"supportedLngs: {supported}", new)
    if new != txt:
        i18n_js.write_text(new)
        _chown_to_owner(i18n_js, backend_root)
        return True
    return False


def _update_env(backend_root: Path, updates: dict) -> None:
    """Upsert keys into the base .env (backend/migratis/.env), preserving other
    lines and order. Only non-empty values are written. Persists the EMAIL_*/
    STRIPE_* settings collected by the install wizard."""
    updates = {k: v for k, v in (updates or {}).items() if v not in (None, '')}
    if not updates:
        return
    env_path  = backend_root / 'migratis' / '.env'
    lines     = env_path.read_text().splitlines() if env_path.exists() else []
    remaining = dict(updates)
    out = []
    for line in lines:
        key = line.split('=', 1)[0].strip() if '=' in line else ''
        if key in remaining:
            out.append(f'{key}={remaining.pop(key)}')
        else:
            out.append(line)
    for key, val in remaining.items():
        out.append(f'{key}={val}')
    env_path.write_text('\n'.join(out) + '\n')
    _chown_to_owner(env_path, backend_root)


def _set_frontend_stripe_key(backend_root: Path, frontend_root: Path, pub_key: str):
    """Override the publishable STRIPE_API_KEY literal in frontend/src/settings.js."""
    if not pub_key:
        return
    settings_js = frontend_root / 'settings.js'
    if not settings_js.exists():
        return
    txt = settings_js.read_text()
    new = re.sub(
        r"(export const STRIPE_API_KEY\s*=\s*).*?(;)",
        lambda m: f'{m.group(1)}"{pub_key}"{m.group(2)}',
        txt, count=1,
    )
    if new != txt:
        settings_js.write_text(new)
        _chown_to_owner(settings_js, backend_root)


def _apply_install_config(backend_root: Path, frontend_root: Path, config: dict) -> dict:
    """Apply the wizard config: write EMAIL_*/STRIPE_* to .env, set the frontend
    publishable key, and return the admin credentials to defer for superuser
    creation (the user tables don't exist until migrate runs). Returns {} when no
    admin was supplied."""
    config = config or {}
    env_updates = {}
    env_updates.update(config.get('email') or {})
    stripe = config.get('stripe') or {}
    env_updates.update({k: v for k, v in stripe.items() if k != 'STRIPE_API_KEY'})
    _update_env(backend_root, env_updates)

    if frontend_root.exists():
        _set_frontend_stripe_key(backend_root, frontend_root, stripe.get('STRIPE_API_KEY', ''))

    admin = config.get('admin') or {}
    if admin.get('email') and admin.get('password'):
        return {'email': admin['email'], 'password': admin['password']}
    return {}


def _remove_module(module: str, backend_root: Path) -> dict:
    """
    Reverse _apply_package for a given module.
    """
    frontend_root = Path(getattr(settings, 'FRONTEND_SRC_DIR', '/frontend/src'))
    patches_dir   = _patches_dir(backend_root)

    # ── 0. Fix any broken migration imports (e.g. `import backend.<module>.*`)
    #       and clear __pycache__ so Python doesn't use stale .pyc files.
    migrations_dir = backend_root / module / 'migrations'
    if migrations_dir.exists():
        for mig in migrations_dir.glob('*.py'):
            try:
                txt = mig.read_text()
                if 'backend.' in txt:
                    mig.write_text(txt.replace('backend.', ''))
            except OSError:
                pass
        pycache = migrations_dir / '__pycache__'
        if pycache.exists():
            shutil.rmtree(pycache, ignore_errors=True)
    # Also clear the module-level __pycache__
    mod_pycache = backend_root / module / '__pycache__'
    if mod_pycache.exists():
        shutil.rmtree(mod_pycache, ignore_errors=True)

    # ── 1. Migrate to zero ────────────────────────────────────────────────
    # Must run while the app directory and settings patch still exist so that
    # Django can find migration files and the app is in INSTALLED_APPS.
    migrate = subprocess.run(
        ['python', 'manage.py', 'migrate', module, 'zero'],
        cwd=str(backend_root), capture_output=True, text=True, timeout=120,
    )

    # ── 2. Delete settings patch file FIRST ───────────────────────────────
    # Deleting the patch removes the app from INSTALLED_APPS before the app
    # directory is removed. The StatReloader fires here and reloads Django
    # cleanly (no app, no migration warning). Deleting the directory afterwards
    # triggers at most another harmless reload.
    for fname in [f'{module}.py', f'{module}_additions.json', f'{module}_manifest.json']:
        f = patches_dir / fname
        if f.exists():
            f.unlink()

    # ── 2b. Re-comment framework routers no longer needed ─────────────────
    # Install uncomments routers in api/views.py; mirror that on uninstall so we
    # never import models for an app that has just left INSTALLED_APPS (which
    # Django reports as "Model ... doesn't declare an explicit app_label").
    # Runs after the patch file is deleted so the active-app scan reflects the
    # removal, and before the app directory is gone.
    _sync_framework_routers(backend_root)

    # ── 2c. Reconcile feature flags + language for the remaining apps ──────
    # Mirror install: turn flags back off and revert the default language once no
    # remaining app needs them (resets to base 'en' when the last app is removed).
    _write_language_patch(backend_root)
    if frontend_root.exists():
        _sync_frontend_flags(backend_root, frontend_root)
        _sync_frontend_language(backend_root, frontend_root)

    # ── 3. Remove backend app directory ───────────────────────────────────
    app_dir = backend_root / module
    if app_dir.exists():
        shutil.rmtree(app_dir)

    # ── 4. Remove frontend module directory ───────────────────────────────
    frontend_ok = False
    module_dir  = frontend_root / module
    if module_dir.exists():
        shutil.rmtree(module_dir)
        frontend_ok = True

    # ── 5. Rebuild module_registry.js (without the removed module) ────────
    if frontend_root.exists():
        _rebuild_registry(backend_root, frontend_root)
        frontend_ok = True

    return {
        'success':          True,
        'module':           module,
        'frontend_ok':      frontend_ok,
        'migrate_ok':       migrate.returncode == 0,
        'migrate_output':   (migrate.stdout or migrate.stderr)[-1000:],
        # See _apply_package: in dev the autoreloader reloads on the api/views.py
        # change; only production requires a manual restart to drop the module.
        'restart_required': not _backend_autoreloads(),
    }


def _build_install_instructions(module: str, additions: dict) -> str:
    imports = '\n'.join(additions.get('imports', []))
    routes  = '\n'.join(additions.get('routes',  []))
    return (
        f"# Frontend install — {module}\n\n"
        f"## 1. Copy files\n"
        f"Extract the `src/` folder into `frontend/src/`.\n\n"
        f"## 2. module_registry.js is updated automatically by the installer.\n\n"
        f"## 3. Restart the frontend\n"
        f"```bash\nnpm start\n```\n"
    )
