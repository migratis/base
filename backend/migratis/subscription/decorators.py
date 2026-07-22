from functools import wraps
from django.conf import settings

from . import models

def test_access(user):
    if settings.NO_SUBSCRIPTION:
        return True

    access = models.Subscription.objects.select_related("user").filter(user=user.id, access=True)
    if access:
        return True
    return False

class AccessDenied(Exception):
    """Raised by `check_access` when the entitlement provider blocks a request.

    Raising (rather than returning a response) lets the denial short-circuit the
    view *before* any wrapping machinery runs — notably django-ninja's
    `RouterPaginated`, which would otherwise try to paginate/slice the 403
    response object and 500. A registered API exception handler
    (`migratis.api.views`) renders the structured envelope."""

    def __init__(self, result):
        self.result = result
        super().__init__(result.reason or "access-denied")


def check_access(action=None):
    """Gate an endpoint behind the entitlement seam.

    Optionally tag the call with an `action` (e.g. ``"generate"``) so a pluggable
    provider can make per-action decisions. On a block it raises `AccessDenied`,
    which the API exception handler renders as a structured, machine-readable 403
    (the `EntitlementResult.payload()` under ``entitlement``) so the agent can
    branch on a code; the ``detail`` envelope is kept so the human lane's 403
    handling is unchanged. Raising (vs returning a response) means the block
    short-circuits before view-wrapping machinery like `RouterPaginated` runs."""
    def decorator(view):
        @wraps(view)
        def _wrapped_view(request, *args, **kwargs):
            # Imported lazily: entitlement imports test_access from this module.
            from .entitlement import check_entitlement
            result = check_entitlement(request, action=action)
            if not result.allowed:
                raise AccessDenied(result)
            return view(request, *args, **kwargs)
        return _wrapped_view
    return decorator