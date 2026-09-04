"""Neutral billing facade.

Lets the `user` module (and any other framework code) integrate with the
optional `subscription` app without importing it at module-load time. Every
helper returns a safe default when subscriptions are unavailable and lazily
delegates to `subscription` only when there is something to delegate to — so
`user` runs standalone, with no `subscription` in INSTALLED_APPS.

**The question is whether the app is installed, not whether a flag is set.**
This asked `settings.NO_SUBSCRIPTION`, which defaults to `False` — so on a base
install with `subscription` commented out of INSTALLED_APPS (the shipped state)
every helper here would go ahead and import it, and the deferred import chain
reaches `stripe_payment.models.Customer`, a model in an app that is not
installed. `apps.is_installed` cannot get out of step with INSTALLED_APPS the
way an operator-set flag can, and it needs nobody to remember anything.

`NO_SUBSCRIPTION` survives as the deliberate override: installed, but off.
"""
from django.apps import apps
from django.conf import settings


def _disabled():
    """No subscription app to talk to, or one that has been switched off."""
    if not apps.is_installed('migratis.subscription'):
        return True
    return getattr(settings, 'NO_SUBSCRIPTION', False)


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


def stripe_error_dict(error):
    """formatErrors() dict for a failed save_customer — safe when billing is
    off (that path never produces an error to map)."""
    if _disabled():
        return {"stripe": ["payment-service-unavailable"]}
    from migratis.subscription.views import stripeErrorDict
    return stripeErrorDict(error)


def active_subscription(user):
    """The user's active Subscription instance, or None (always None when off)."""
    if _disabled():
        return None
    from migratis.subscription.models import Subscription
    try:
        return Subscription.objects.get(user=getattr(user, 'id', user), access=True)
    except Subscription.DoesNotExist:
        return None
