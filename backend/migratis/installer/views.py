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
from pathlib import Path

import requests as http_requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from ninja import Router

router = Router()

MIGRATIS_BACKEND_URL = getattr(settings, 'MIGRATIS_BACKEND_URL', 'http://host.docker.internal:8000')

_FRAMEWORK_MODULES = frozenset([
    'user', 'i18n', 'cookie', 'support', 'subscription', 'generator', 'installer',
])


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


def _get_installed_modules(backend_root: Path) -> list:
    """Return modules that have a settings_patches/<module>.py file."""
    d = _patches_dir(backend_root)
    if not d.exists():
        return []
    return sorted(
        p.stem for p in d.glob('*.py')
        if p.stem != '__init__' and p.stem not in _FRAMEWORK_MODULES
    )


def _rebuild_registry(backend_root: Path, frontend_root: Path):
    """
    Regenerate module_registry.js from all *_additions.json files
    in settings_patches/. Called after every install and uninstall.
    """
    registry_path = frontend_root / 'module_registry.js'
    if not registry_path.exists():
        return  # frontend volume not mounted

    import_re = re.compile(
        r"^const (\w+) = lazyWithRetry\(\(\) => import\('([^']+)'\)\);?$"
    )
    route_re = re.compile(r'path="([^"]+)"[^>]*element=\{<(\w+)\s*/?>}')

    all_imports = []   # [(component_name, import_path), ...]
    all_routes  = []   # [(url_path, component_name), ...]
    all_menu    = []   # [{"label": ..., "path": ...}, ...]

    patches_dir = _patches_dir(backend_root)
    for additions_file in sorted(patches_dir.glob('*_additions.json')):
        additions = json.loads(additions_file.read_text())
        module    = additions.get('module', additions_file.stem.replace('_additions', ''))

        for imp in additions.get('imports', []):
            m = import_re.match(imp.strip())
            if m:
                all_imports.append((m.group(1), m.group(2)))

        for route in additions.get('routes', []):
            m = route_re.search(route)
            if m:
                all_routes.append((m.group(1), m.group(2)))

        all_menu.extend(additions.get('menu_items', []))

    lines = []
    if all_imports:
        lines.append("import { lazyWithRetry } from './common/tools/lazyWithRetry';")
        lines.append('')
        prev_module = None
        for name, imp_path in all_imports:
            # Add a comment separator when the module changes
            module_guess = imp_path.split('/')[1] if imp_path.startswith('./') else ''
            if module_guess != prev_module:
                lines.append(f"// ── {module_guess} ──")
                prev_module = module_guess
            lines.append(f"const {name} = lazyWithRetry(() => import('{imp_path}'));")
        lines.append('')

    routes_js = ',\n  '.join(
        f'{{ path: "{p}", Component: {c} }}' for p, c in all_routes
    ) if all_routes else ''
    lines.append(f"export const moduleRoutes = [{f'{chr(10)}  {routes_js},{chr(10)}' if routes_js else ''}];")
    lines.append('')

    menu_js = ',\n  '.join(
        f'{{ label: "{item["label"]}", path: "{item["path"]}" }}' for item in all_menu
    ) if all_menu else ''
    lines.append(f"export const moduleMenuItems = [{f'{chr(10)}  {menu_js},{chr(10)}' if menu_js else ''}];")
    lines.append('')

    registry_path.write_text('\n'.join(lines))


# --------------------------------------------------------------------------- #
# Auth endpoints
# --------------------------------------------------------------------------- #

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

    try:
        s    = http_requests.Session()
        resp = s.post(
            f'{url}/backend/api/user/login',
            data={'email': email, 'password': password},
            timeout=10,
        )
    except Exception:
        return JsonResponse({'detail': [{'url': ['connection-failed']}]}, status=503)

    if resp.status_code != 200:
        return JsonResponse({
            'detail': [{'credentials': ['invalid-credentials']}],
            '_debug': {'status': resp.status_code, 'body': resp.text[:500]},
        }, status=401)

    request.session['migratis_cookies'] = dict(s.cookies)
    request.session['migratis_url']     = url
    request.session.modified            = True

    return JsonResponse({'user': resp.json().get('user', {})})


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

    if resp.status_code != 200:
        return JsonResponse({'detail': [{'session': ['not-connected']}]}, status=401)

    apps = [a for a in resp.json().get('items', []) if a.get('status') == 'generated']
    return JsonResponse({'apps': apps})


# --------------------------------------------------------------------------- #
# Installation
# --------------------------------------------------------------------------- #

@router.post('/install/{app_id}', auth=None)
def installer_install(request, app_id: int):
    s, url = _session(request)
    if s is None:
        return JsonResponse({'detail': [{'session': ['not-connected']}]}, status=401)

    try:
        resp = s.get(f'{url}/backend/api/generator/application/{app_id}/download', timeout=60)
    except Exception:
        return JsonResponse({'detail': [{'download': ['download-failed']}]}, status=503)

    if resp.status_code != 200:
        return JsonResponse({'detail': [{'download': ['download-failed']}]}, status=resp.status_code)

    try:
        result = _apply_package(resp.content)
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
# Package application logic
# --------------------------------------------------------------------------- #

def _apply_package(zip_bytes: bytes) -> dict:
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
                # Fix `import backend.<module>.*` in migration files
                if '/migrations/' in name:
                    content = content.replace(b'backend.', b'')
                # Fix `from ninja.files import File` → `from ninja import File`
                content = content.replace(
                    b'from ninja.files import File',
                    b'from ninja import File',
                )
            dest.write_bytes(content)
            installed_files.append(f'backend/{rel}')

        # ── 2. Framework router activation (idempotent uncomment) ─────────
        api_views  = backend_root / 'migratis' / 'api' / 'views.py'
        api_txt    = api_views.read_text()
        modules_needed = manifest.get('modules_needed', [])
        _FRAMEWORK_ROUTERS = [
            ('user',         'user_router',         'migratis.user.views',         '/user/'),
            ('i18n',         'i18n_router',         'migratis.i18n.views',         '/i18n/'),
            ('cookie',       'cookie_router',       'migratis.cookie.views',       '/cookie/'),
            ('support',      'support_router',      'migratis.support.views',      '/support/'),
            ('subscription', 'subscription_router', 'migratis.subscription.views', '/subscription/'),
        ]
        changed = False
        for key, rname, rmod, rpath in _FRAMEWORK_ROUTERS:
            if key not in modules_needed:
                continue
            if f'# from {rmod} import router as {rname}' in api_txt:
                api_txt = api_txt.replace(
                    f'# from {rmod} import router as {rname}',
                    f'from {rmod} import router as {rname}',
                )
                changed = True
            if f'# api.add_router("{rpath}", {rname})' in api_txt:
                api_txt = api_txt.replace(
                    f'# api.add_router("{rpath}", {rname})',
                    f'api.add_router("{rpath}", {rname})',
                )
                changed = True
        if changed:
            api_views.write_text(api_txt)

        # ── 3. Settings patch file (idempotent) ────────────────────────────
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

        # ── 4. Frontend additions metadata ────────────────────────────────
        additions = {}
        if 'frontend/app_additions.json' in names:
            additions = json.loads(zf.read('frontend/app_additions.json'))
            additions_file = patches_dir / f'{module}_additions.json'
            additions_file.write_text(json.dumps(additions, indent=2, ensure_ascii=False))

        # ── 5. Frontend source files ───────────────────────────────────────
        frontend_ok = False
        if frontend_root.exists():
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
            frontend_ok = True

            # ── 6. Rebuild module_registry.js ─────────────────────────────
            _rebuild_registry(backend_root, frontend_root)

        # ── 7. Fix ownership — chown written files back to the volume owner ─
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

        # ── 8. Defer migrate + seed to InstallerConfig.ready() ────────────
        # Writing apps.py in step 1 triggers StatReloader within ~1 s, which
        # kills this request handler before subprocess.run(['migrate']) could
        # complete.  Instead, write a marker that InstallerConfig.ready()
        # picks up on the very next startup (after StatReloader restarts).
        pending = patches_dir / '_pending_install.json'
        pending.write_text(json.dumps({'module': module}))
        if uid != 0:
            try:
                os.chown(pending, uid, gid)
            except OSError:
                pass

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
        'restart_required': True,
    }


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
    for fname in [f'{module}.py', f'{module}_additions.json']:
        f = patches_dir / fname
        if f.exists():
            f.unlink()

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
        'restart_required': True,
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
