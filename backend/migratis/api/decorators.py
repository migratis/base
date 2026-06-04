"""Cross-cutting access-control decorator.

`check_access` lives here (not in the optional `subscription` app) so that any
framework or generated module can guard its endpoints without making
`subscription` a hard dependency. Subscription enforcement is consulted lazily,
and only when it is actually enabled (NO_SUBSCRIPTION is False).
"""
from functools import wraps
from django.conf import settings
from ninja.errors import HttpError


def test_access(user):
    # When subscriptions are disabled the gate is open for every authenticated
    # user — the `subscription` app need not even be installed.
    if settings.NO_SUBSCRIPTION:
        return True
    # Enforcing subscriptions: consult the (now-required) subscription app lazily
    # so importing this module never pulls subscription models into scope.
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
