from ninja import NinjaAPI
from ninja.security import django_auth
from ninja.renderers import BaseRenderer
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
# ── Activated by generated app settings_patch.py ──────────────────────────
# from migratis.user.views import router as user_router
from migratis.i18n.views import router as i18n_router
from migratis.cookie.views import router as cookie_router
# from migratis.support.views import router as support_router
# from migratis.subscription.views import router as subscription_router
# from migratis.generator.views import router as generator_router
from migratis.installer.views import router as installer_router
import datetime
import decimal
import importlib
import json

from django.conf import settings as django_settings


class CustomEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, datetime.date):
            return str(o)
        elif isinstance(o, decimal.Decimal):
            return float(o)
        else:
            try:
                obj = o.decode()
                return obj
            except (UnicodeDecodeError, AttributeError):
                return json.JSONEncoder.default(self, o)


class CustomRenderer(BaseRenderer):
    media_type = "text/plain"

    def render(self, request, data, *, response_status):
        return json.dumps(data, cls=CustomEncoder)


api = NinjaAPI(auth=django_auth, renderer=CustomRenderer())

# ── Activated by generated app settings_patch.py ──────────────────────────
# api.add_router("/user/", user_router)
api.add_router("/i18n/",    i18n_router)
api.add_router("/cookie/",  cookie_router)
# api.add_router("/support/", support_router)
# api.add_router("/subscription/", subscription_router)
# api.add_router("/generator/", generator_router)
api.add_router("/installer/", installer_router)

# ── Auto-mount routers for installed apps ─────────────────────────────────
_FRAMEWORK_APPS = frozenset([
    'user', 'i18n', 'cookie', 'support', 'subscription', 'generator', 'installer',
])
for _app in django_settings.INSTALLED_APPS:
    if '.' not in _app and _app not in _FRAMEWORK_APPS:
        try:
            _mod = importlib.import_module(f'{_app}.views')
            if hasattr(_mod, 'router'):
                api.add_router(f'/{_app}/', _mod.router)
        except ImportError:
            pass


@api.get("/csrftoken")
def get_csrf(request):
    return render(request, 'csrftoken.html', context={})


@api.get("/", auth=None)
def index(request):
    return render(request, 'index.html', context={})


@api.get("/home", auth=None)
def home(request):
    return ""


@api.get("/ping", auth=None)
def ping(request):
    return JsonResponse({'result': 'OK'})


@ensure_csrf_cookie
@api.get("/session", auth=None)
def session(request):
    if not request.user.is_authenticated:
        return JsonResponse({'isAuthenticated': False})
    return JsonResponse({'isAuthenticated': True})


@api.get("/whoami")
def whoami(request):
    if not request.user.is_authenticated:
        return JsonResponse({'isAuthenticated': False})
    return JsonResponse({'username': request.user.username})


@login_required
def openapi_view(request):
    with open('/openapi.json') as f:
        openapi_data = json.load(f)
    return JsonResponse(openapi_data)
