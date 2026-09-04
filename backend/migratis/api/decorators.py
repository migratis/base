"""Cross-cutting access-control decorator.

`check_access` lives here (not in the optional `subscription` app) so that any
framework or generated module can guard its endpoints without making
`subscription` a hard dependency. Subscription enforcement is consulted lazily,
and only when there is a subscription app to consult.

**Installed, not flagged** — see `migratis.api.billing._disabled`. Asking
`NO_SUBSCRIPTION` (default `False`) meant an install without the subscription
app still tried to import its models.
"""
from functools import wraps
from ninja.errors import HttpError

from . import billing


def test_access(user):
    # No subscription app, or one switched off: the gate is open for every
    # authenticated user — `subscription` need not even be installed.
    if billing._disabled():
        return True
    # Enforcing: consult the subscription app lazily, so importing this module
    # never pulls subscription models into scope.
    from migratis.subscription.models import Subscription
    return Subscription.objects.filter(user=getattr(user, 'id', user), access=True).exists()


def check_access():
    def decorator(view):
        @wraps(view)
        def _wrapped_view(request, *args, **kwargs):
            if not test_access(request.user):
                raise HttpError(403, "Forbidden")
            return view(request, *args, **kwargs)
        return _wrapped_view
    return decorator
