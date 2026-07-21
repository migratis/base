"""Credit balance operations — shared by every credit-spending call site.

Moved out of generator (was the credit helpers in ``ai_usage_tracker.py``) and
de-AI'd. The optional subscription bypass is a *soft* dependency: it lazily
imports the subscription app and fails safe (falls back to the credit path) when
it is absent or errors, so credits stays installable on its own.

NOTE: the free-tier size still comes from ``settings.CREDITS_FREE_TIER_LIMIT`` — the
credit settings are renamed to ``CREDITS_*`` in P4.
"""
from django.conf import settings

from .models import CreditBalance, CreditCost


def get_or_create_balance(user):
    """Get or create the user's CreditBalance, seeding with the free-tier amount."""
    balance, created = CreditBalance.objects.get_or_create(user=user)
    if created:
        balance.credits = getattr(settings, 'CREDITS_FREE_TIER_LIMIT', 10)
        balance.save(update_fields=['credits'])
    return balance


def get_operation_cost(operation):
    """Return the credit cost for an operation; defaults to 1 if not configured."""
    try:
        return CreditCost.objects.get(operation=operation).credits
    except CreditCost.DoesNotExist:
        return 1


def has_active_subscription(user):
    """True when the user holds a subscription that currently grants access.

    Keyed on a REAL active `Subscription` (access=True), independent of the
    `NO_SUBSCRIPTION` flag (that flag only governs the `check_access` endpoint
    gate). A subscriber bypasses the credit requirement entirely — human AND
    agent lane (owner decision 2026-07-20). Lazily imports the subscription app
    so credits does not hard-depend on it."""
    if user is None or not getattr(user, "id", None):
        return False
    try:
        from migratis.subscription.models import Subscription
        return Subscription.objects.filter(user=user.id, access=True).exists()
    except Exception:
        # A subscription lookup failure must never harden into a credit block;
        # fall back to the credit path (fail-closed on the bypass, not the gate).
        return False


def has_credits(user, operation=None, amount=1):
    """Return (ok, balance). ok is True when the user can cover
    `amount` × cost(operation). Default amount=1 keeps prior behaviour for
    single-call sites. An active subscription bypasses the check entirely."""
    balance = get_or_create_balance(user)
    if has_active_subscription(user):
        return True, balance
    cost = (get_operation_cost(operation) if operation else 1) * max(int(amount), 0)
    return balance.credits >= cost, balance


def debit_credits(user, operation=None, amount=1):
    """Debit by cost(operation) × amount. Default amount=1. An active
    subscription is never debited (unlimited access)."""
    balance = get_or_create_balance(user)
    if has_active_subscription(user):
        return balance
    cost = (get_operation_cost(operation) if operation else 1) * max(int(amount), 0)
    balance.decrement(cost)
    return balance
