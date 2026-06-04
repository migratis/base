"""Neutral billing facade.

Lets the `user` module (and any other framework code) integrate with the
optional `subscription` app without importing it at module-load time. Every
helper returns a safe default when subscriptions are disabled (NO_SUBSCRIPTION)
and lazily delegates to `subscription` only when enforcement is enabled — so
`user` runs standalone, with no `subscription` in INSTALLED_APPS.
"""
from django.conf import settings


def _disabled():
    return settings.NO_SUBSCRIPTION


def has_trial(user):
    if _disabled():
        return True
    from migratis.subscription.views import hasTrial
    return hasTrial(user)


def has_access(user):
    if _disabled():
        return False
    from migratis.subscription.views import hasAccess
    return hasAccess(user)


def do_unsubscribe(user_id):
    if _disabled():
        return {'detail': [{'success': ['unsubscribe-successfully']}]}
    from migratis.subscription.views import doUnsubscribe
    return doUnsubscribe(user_id)


def save_customer(user):
    # Returns a (saved, error) tuple — a no-op success when billing is off.
    if _disabled():
        return True, None
    from migratis.subscription.views import saveCustomer
    return saveCustomer(user)


def active_subscription(user):
    """The user's active Subscription instance, or None (always None when off)."""
    if _disabled():
        return None
    from migratis.subscription.models import Subscription
    try:
        return Subscription.objects.get(user=getattr(user, 'id', user), access=True)
    except Subscription.DoesNotExist:
        return None
