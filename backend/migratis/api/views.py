from ninja import NinjaAPI
from ninja.security import django_auth
from ninja.renderers import BaseRenderer
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.conf import settings as django_settings
# ── Activated by generated app settings_patch.py ──────────────────────────
# from migratis.user.views import router as user_router
from migratis.i18n.views import router as i18n_router
from migratis.cookie.views import router as cookie_router
# from migratis.support.views import router as support_router
# from migratis.subscription.views import router as subscription_router
# from migratis.stripe_payment.views import router as stripe_payment_router
# from migratis.credits.views import router as credits_router
# from migratis.routing.views import router as routing_router
# from migratis.generator.views import router as generator_router
from migratis.api.functions import formatErrors as _formatErrors
from migratis.installer.views import router as installer_router
import datetime
import decimal
import importlib
import json

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


from migratis.installer.agent_guide import render_installer_guide_markdown

api = NinjaAPI(
    title="Migratis base",
    version="1.0.0",
    # The installer agent lane (how to install a generated package) rides in the
    # public OpenAPI info.description, so an agent reading the schema discovers
    # the procedure for free. Same source as GET /installer/agent-guide.
    description=render_installer_guide_markdown(),
    auth=django_auth,
    renderer=CustomRenderer(),
)

# Register the entitlement-denial handler only when the subscription app is
# actually installed. base activates subscription/stripe_payment on demand via
# settings_patches, so importing decorators unconditionally would pull in
# stripe_payment.models at startup and crash ("doesn't declare an explicit
# app_label and isn't in an application in INSTALLED_APPS") on deployments that
# ship without those apps.
try:
    from migratis.subscription.decorators import AccessDenied as _AccessDenied

    @api.exception_handler(_AccessDenied)
    def _access_denied(request, exc):
        return JsonResponse({
            "detail": _formatErrors({"access": ["access-denied"]}),
            "entitlement": exc.result.payload(),
        }, status=403)
except (ImportError, RuntimeError):
    pass

# ── Activated by generated app settings_patch.py ──────────────────────────
# api.add_router("/user/", user_router)
api.add_router("/i18n/",    i18n_router)
api.add_router("/cookie/",  cookie_router)
# api.add_router("/support/", support_router)
# api.add_router("/subscription/", subscription_router)
# api.add_router("/billing/", stripe_payment_router)
# api.add_router("/credits/", credits_router)
# api.add_router("/routing/", routing_router)
# api.add_router("/generator/", generator_router)
# The installer is mounted only when enabled (INSTALLER setting), so its
# endpoints are not reachable on deployments that ship without it.
if django_settings.INSTALLER:
    api.add_router("/installer/", installer_router)

# ── Auto-mount routers for installed apps ─────────────────────────────────
_FRAMEWORK_APPS = frozenset([
    'user', 'i18n', 'cookie', 'support', 'subscription', 'credits', 'routing',
    'generator', 'installer',
])
for _app in django_settings.INSTALLED_APPS:
    if '.' not in _app and _app not in _FRAMEWORK_APPS:
        try:
            _mod = importlib.import_module(f'{_app}.views')
            if hasattr(_mod, 'router'):
                api.add_router(f'/{_app}/', _mod.router)
        except ImportError:
            pass


@api.get("/installer/status", auth=None)
def installer_status(request):
    """Always-available flag (even when the installer router is unmounted) so the
    frontend can show how to reactivate the installer when it is disabled. When
    enabled, points agents at the self-describing install guide so discovery can
    start from the one always-on endpoint."""
    body = {'enabled': django_settings.INSTALLER}
    if django_settings.INSTALLER:
        body['agent_guide'] = '/backend/api/installer/agent-guide'
    return JsonResponse(body)


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


@api.get("/status", auth=None)
def status(request):
    """Live self-check behind the public /status page.

    Deliberately *not* an uptime history — nothing here is recorded or averaged
    over time. Every field is measured at the instant of the request, so the
    page can never claim a health it has not just verified:

    * ``api``      — implicit: this view answered.
    * ``database`` — a trivial round-trip to Postgres.
    * ``routing`` — the road-routing engine, when one is configured. A host
      that configured none is not a host with a broken engine, so the row is
      omitted entirely rather than reported down (same rule as an LLM provider
      with no API key). Present-and-unavailable is the state that matters: the
      module is installed, the map still works, and every route it draws is a
      straight line until the engine comes back.
    * ``services`` — one entry per LLM provider that is actually configured (an
      unset API key means the provider is not offered at all, so it is omitted
      rather than reported down). ``operational`` unless that provider's
      circuit breaker is tripped, which is exactly what makes it disappear from
      the model picker. Empty where the generator module is not installed —
      it is optional, and a deployment without it has no AI to report on.

    Only labels and states are published — never the breaker reason, which can
    quote a provider's billing error verbatim.
    """
    from django.db import connection

    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        database = 'operational'
    except Exception:                     # pragma: no cover - infrastructure
        database = 'unavailable'

    services = []
    try:
        # The generator is an optional module; without it there are no AI
        # providers to report and the platform section stands alone.
        from migratis.generator import llm

        catalog = llm.providers()
        for code, provider in catalog.items():
            if not llm.provider_api_key(code, catalog):
                continue
            services.append({
                'code': code,
                'label': provider.get('label') or code,
                'state': ('operational' if llm.provider_available(code, catalog)
                          else 'unavailable'),
            })
    except ImportError:
        pass

    routing = None
    try:
        # Optional module, and optional even when installed — see the docstring.
        # Only the state is published, never the engine's own error, which
        # quotes internal hostnames.
        from migratis.routing.services import engine_state

        routing_state, routing_engine = engine_state()
        if routing_state != 'not_configured':
            routing = {'engine': routing_engine, 'state': routing_state}
    except Exception:                     # pragma: no cover - optional module
        pass

    degraded = database != 'operational' or any(
        service['state'] != 'operational' for service in services
    )
    if routing is not None and routing['state'] != 'operational':
        degraded = True

    payload = {
        'api': 'operational',
        'database': database,
        'services': services,
        'state': 'degraded' if degraded else 'operational',
        'checked_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    if routing is not None:
        payload['routing'] = routing
    return JsonResponse(payload)

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
