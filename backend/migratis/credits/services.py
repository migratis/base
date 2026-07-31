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
from decimal import Decimal

from django.conf import settings

from .models import CreditBalance, CreditCost, quantize_credits


def get_or_create_balance(user):
    """Get or create the user's CreditBalance, seeding with the free-tier amount."""
    balance, created = CreditBalance.objects.get_or_create(user=user)
    if created:
        balance.credits = Decimal(str(getattr(settings, 'CREDITS_FREE_TIER_LIMIT', 10)))
        balance.save(update_fields=['credits'])
    return balance


def get_operation_cost(operation):
    """Return the credit cost for an operation; defaults to 1 if not configured.

    This is the *base* cost — what the operation costs on the reference model.
    Scaling it for the model that actually served the call is the caller's job
    (see `multiplier` below)."""
    try:
        return CreditCost.objects.get(operation=operation).credits
    except CreditCost.DoesNotExist:
        return Decimal('1')


def charge_for(operation=None, amount=1, multiplier=None):
    """The exact amount to charge: base cost × amount × multiplier, rounded to
    the credit's smallest unit.

    `multiplier` is the per-model coefficient — how much more (or less) the
    model that served this call costs than the reference model. It is passed in
    rather than looked up because this app must not know that LLMs exist: that
    is what lets `credits` install without the generator. Leave it out wherever
    Migratis called no model of its own (agent-lane prompt kinds, component
    adoptions), and the flat cost stands.

    A positive charge never rounds away to zero — see `quantize_credits`.

    `amount` is Decimal-safe on purpose. It is usually a whole count of units,
    but the agent-lane approval bill passes a pre-computed total through it, and
    now that an operation can cost a fraction that total can be fractional too —
    truncating it to an int would quietly undercharge every bill that did not
    land on a whole credit.
    """
    base = get_operation_cost(operation) if operation else Decimal('1')
    units = max(Decimal(str(amount)), Decimal('0'))
    total = Decimal(base) * units
    if multiplier is not None:
        total *= Decimal(str(multiplier))
    return quantize_credits(total, floor_at_smallest_unit=units > 0)


def has_credits(user, operation=None, amount=1, multiplier=None):
    """Return (ok, balance). ok is True when the user's balance can cover
    `amount` × cost(operation) × `multiplier`. Default amount=1 keeps prior
    behaviour for single-call sites. Pure credit check — no subscription
    concept here.

    Must be priced identically to `debit_credits`, which is why both go through
    `charge_for`: a check that disagrees with the debit either blocks a call the
    user can afford or lets through one they cannot."""
    balance = get_or_create_balance(user)
    return balance.credits >= charge_for(operation, amount, multiplier), balance


def debit_credits(user, operation=None, amount=1, multiplier=None):
    """Debit the balance by cost(operation) × amount × multiplier. Default
    amount=1. Pure credit op — always charges (any "subscription covers it"
    decision is made by the caller before this is reached)."""
    balance = get_or_create_balance(user)
    balance.decrement(charge_for(operation, amount, multiplier))
    return balance
