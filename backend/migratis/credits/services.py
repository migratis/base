"""Credit balance operations — shared by every credit-spending call site.

Moved out of generator (was the credit helpers in ``ai_usage_tracker.py``) and
de-AI'd.

**Subscription-agnostic (owner 2026-07-22).** These are *pure* credit ops: they
only ever price and charge against the user's balance. The "an active
subscription covers this charge" decision is NOT made here — it is a
migratis-generator specificity that composes the optional ``credits`` and
``subscription`` modules and lives in ``migratis.generator.monetization``. Keeping
``credits`` free of any subscription import is what makes it base-syncable and
independently installable.

NOTE: the free-tier size still comes from ``settings.CREDITS_FREE_TIER_LIMIT``.
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


def has_credits(user, operation=None, amount=1):
    """Return (ok, balance). ok is True when the user's balance can cover
    `amount` × cost(operation). Default amount=1 keeps prior behaviour for
    single-call sites. Pure credit check — no subscription concept here."""
    balance = get_or_create_balance(user)
    cost = (get_operation_cost(operation) if operation else 1) * max(int(amount), 0)
    return balance.credits >= cost, balance


def debit_credits(user, operation=None, amount=1):
    """Debit the balance by cost(operation) × amount. Default amount=1. Pure
    credit op — always charges (any "subscription covers it" decision is made by
    the caller before this is reached)."""
    balance = get_or_create_balance(user)
    cost = (get_operation_cost(operation) if operation else 1) * max(int(amount), 0)
    balance.decrement(cost)
    return balance
