"""
installer/views.py
------------------
Endpoints that proxy auth to a remote Migratis generator instance,
list the user's generated applications, download them and install
the backend portion directly into this base project.

Endpoints (all under /backend/api/installer/):
    POST   /connect          — authenticate against Migratis, store session
    DELETE /connect          — clear stored session
    GET    /session          — check whether a session is stored
    GET    /apps             — list generated apps from Migratis
    POST   /install/{id}     — download ZIP + apply backend files + migrate
    GET    /frontend-zip/{id}— stream frontend-only ZIP for manual extraction
"""

import io
import json
import subprocess
import zipfile
from pathlib import Path

import requests as http_requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from ninja import Router

router = Router()

MIGRATIS_BACKEND_URL = getattr(settings, 'MIGRATIS_BACKEND_URL', 'http://host.docker.internal:8000')


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _session(request):
    """Return a requests.Session loaded from the stored cookies, plus the URL."""
    cookies  = request.session.get('migratis_cookies')
    base_url = request.session.get('migratis_url', MIGRATIS_BACKEND_URL)
    if not cookies:
        return None, base_url
    s = http_requests.Session()
    s.cookies.update(cookies)
    return s, base_url


def _err(key, msg):
    return JsonResponse({'detail': [{key: [msg]}]}, status=400)


# --------------------------------------------------------------------------- #
# Auth endpoints
# --------------------------------------------------------------------------- #

@router.post('/connect', auth=None)
def installer_connect(request):
    """
    Authenticate against the remote Migratis instance.
    Body: { email, password, url (optional) }
    Stores session cookies in Django session for subsequent calls.
    """
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

    user_data = resp.json().get('user', {})
    return JsonResponse({'user': user_data})


@router.delete('/connect', auth=None)
def installer_disconnect(request):
    """Clear the stored Migratis session."""
    request.session.pop('migratis_cookies', None)
    request.session.pop('migratis_url', None)
    return JsonResponse({'success': True})


@router.get('/session', auth=None)
def installer_session(request):
    """Return whether a Migratis session is currently stored."""
    return JsonResponse({'connected': bool(request.session.get('migratis_cookies'))})


# --------------------------------------------------------------------------- #
# App listing
# --------------------------------------------------------------------------- #

@router.get('/apps', auth=None)
def installer_list_apps(request):
    """List all generated applications from the connected Migratis instance."""
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
    """
    Download the generated ZIP from Migratis and install the backend.
    Writes Django app files to disk, patches settings.py and api/views.py,
    runs migrations and seed translations.
    Returns a JSON summary; the frontend ZIP is served separately.
    """
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
    """
    Stream a ZIP containing only the frontend src/ files and app_additions.json,
    so the user can manually extract them into their frontend directory.
    """
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
# Package application logic
# --------------------------------------------------------------------------- #

def _apply_package(zip_bytes: bytes) -> dict:
    """
    Extract a generated package ZIP and apply backend + frontend to this project.
    Steps:
      1. Write all backend/ source files to disk.
      2. Append settings_patch.py to settings.py (idempotent).
      3. Register the new router in api/views.py (idempotent).
      4. Write all frontend/ source files to /frontend/src/ (idempotent).
      5. Inject imports + routes into App.js (idempotent).
      6. Inject menu items into MenuLeft.js (idempotent).
      7. Run `manage.py migrate`.
      8. Run `manage.py seed_<module>`.
    """
    backend_root  = Path(settings.BASE_DIR)
    frontend_root = Path('/frontend/src')
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
            dest.write_bytes(zf.read(name))
            installed_files.append(f'backend/{rel}')

        # ── 2. Settings patch (idempotent) ─────────────────────────────────
        settings_file = backend_root / 'migratis' / 'settings.py'
        settings_txt  = settings_file.read_text()
        marker        = f"INSTALLED_APPS += ['{module}']"
        if marker not in settings_txt:
            patch = zf.read('backend/settings_patch.py').decode('utf-8')
            settings_file.write_text(settings_txt + '\n\n' + patch)

        # ── 3. Router registration in api/views.py (idempotent) ────────────
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
            imp_comment   = f'# from {rmod}.views import router as {rname}'
            imp_active    = f'from {rmod}.views import router as {rname}'
            mount_comment = f'# api.add_router("{rpath}", {rname})'
            mount_active  = f'api.add_router("{rpath}", {rname})'
            if imp_comment in api_txt:
                api_txt = api_txt.replace(imp_comment, imp_active)
                changed = True
            if mount_comment in api_txt:
                api_txt = api_txt.replace(mount_comment, mount_active)
                changed = True

        imp_line   = f'from {module}.views import router as {module}_router'
        mount_line = f'api.add_router("/{module}/", {module}_router)'
        if imp_line not in api_txt:
            anchor  = 'from migratis.installer.views import router as installer_router'
            api_txt = api_txt.replace(anchor, f'{anchor}\n{imp_line}')
            api_txt += f'\n{mount_line}\n'
            changed = True
        if changed:
            api_views.write_text(api_txt)

        # ── 4. Frontend source files ───────────────────────────────────────
        frontend_ok = False
        if frontend_root.exists():
            for name in names:
                if not name.startswith('frontend/src/'):
                    continue
                rel  = name[len('frontend/src/'):]
                if not rel or rel.endswith('/'):
                    continue
                dest = frontend_root / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(zf.read(name))
                installed_files.append(f'frontend/src/{rel}')
            frontend_ok = True

            # ── 5. Inject into App.js (idempotent) ────────────────────────
            additions = {}
            if 'frontend/app_additions.json' in names:
                additions = json.loads(zf.read('frontend/app_additions.json'))

            app_js_path = frontend_root / 'App.js'
            if app_js_path.exists() and additions:
                app_txt = app_js_path.read_text()

                imports_marker = '// MIGRATIS:IMPORTS'
                routes_marker  = '{/* MIGRATIS:ROUTES */}'

                new_imports = '\n'.join(
                    line for line in additions.get('imports', [])
                    if line not in app_txt
                )
                if new_imports and imports_marker in app_txt:
                    app_txt = app_txt.replace(
                        imports_marker,
                        f'{imports_marker}\n{new_imports}',
                    )

                new_routes = '\n          '.join(
                    line for line in additions.get('routes', [])
                    if line not in app_txt
                )
                if new_routes and routes_marker in app_txt:
                    app_txt = app_txt.replace(
                        routes_marker,
                        f'{new_routes}\n          {routes_marker}',
                    )

                app_js_path.write_text(app_txt)

            # ── 6. Inject menu items into MenuLeft.js (idempotent) ─────────
            menu_js_path = frontend_root / 'common' / 'components' / 'MenuLeft.js'
            if menu_js_path.exists() and additions.get('menu_items'):
                menu_txt     = menu_js_path.read_text()
                menu_marker  = '{/* MIGRATIS:MENU_SECTIONS */}'

                menu_sections = []
                for item in additions['menu_items']:
                    label     = item['label']
                    path      = item['path']
                    nav_block = (
                        f'<NavLink to="{path}" '
                        f'className={{({{isActive}}) => `sidebar-item ${{isActive ? \'active\' : \'\'}}`}} '
                        f'onClick={{props.onMobileClose}}>'
                        f'<span className="sidebar-label">{label}</span>'
                        f'</NavLink>'
                    )
                    if nav_block not in menu_txt:
                        menu_sections.append(nav_block)

                if menu_sections and menu_marker in menu_txt:
                    block = '\n'.join(menu_sections)
                    menu_txt = menu_txt.replace(
                        menu_marker,
                        f'{block}\n          {menu_marker}',
                    )
                    menu_js_path.write_text(menu_txt)

        # ── 7. Migrate ─────────────────────────────────────────────────────
        migrate = subprocess.run(
            ['python', 'manage.py', 'migrate', '--run-syncdb'],
            cwd=str(backend_root), capture_output=True, text=True, timeout=120,
        )

        # ── 8. Seed translations ───────────────────────────────────────────
        seed = subprocess.run(
            ['python', 'manage.py', f'seed_{module}'],
            cwd=str(backend_root), capture_output=True, text=True, timeout=60,
        )

    return {
        'success':          True,
        'module':           module,
        'installed_files':  installed_files,
        'manifest':         manifest,
        'frontend_ok':      frontend_ok,
        'migrate_ok':       migrate.returncode == 0,
        'migrate_output':   (migrate.stdout or migrate.stderr)[-2000:],
        'seed_ok':          seed.returncode == 0,
        'seed_output':      (seed.stdout or seed.stderr)[-1000:],
        'restart_required': True,
    }


def _build_install_instructions(module: str, additions: dict) -> str:
    imports = '\n'.join(additions.get('imports', []))
    routes  = '\n'.join(additions.get('routes',  []))
    return (
        f"# Frontend install — {module}\n\n"
        f"## 1. Copy files\n"
        f"Extract the `src/` folder into `frontend/src/`.\n\n"
        f"## 2. Add to App.js — imports (after existing lazyWithRetry imports)\n"
        f"```javascript\n{imports}\n```\n\n"
        f"## 3. Add to App.js — routes (inside <Routes>)\n"
        f"```jsx\n{routes}\n```\n\n"
        f"## 4. Restart the frontend\n"
        f"```bash\nnpm start\n```\n"
    )
