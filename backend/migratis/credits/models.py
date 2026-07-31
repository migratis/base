"""Credit models — a standalone, de-AI'd billing feature.

Relocated from ``generator`` (was ``UserAIUsage`` / ``AICallCost``). Physical
tables are renamed in place (``credits_creditbalance`` / ``credits_creditcost``)
so **no rows move**. The field stays ``credits`` (decision D1); the price table
is keyed on ``call_type`` for now (decoupled to an opaque ``operation`` in P3).

This module imports nothing from ``generator`` — credits is installable on its
own; ``generator`` is a *consumer* of credits, inverting the old coupling.
"""
from decimal import Decimal, ROUND_HALF_UP

from django.db import models

from migratis.user.models import User

# Credits are fractionable: an operation served by a cheap model costs a
# fraction of what the same operation costs on an expensive one, and a whole
# credit is far too coarse a unit to express that. Two decimal places is the
# smallest amount that can be charged, and also the floor — an operation never
# costs nothing, however cheap the model (see `quantize_credits`).
CREDIT_PLACES = Decimal('0.01')


def quantize_credits(amount, floor_at_smallest_unit=False):
    """Round `amount` to the credit's smallest unit, half-up.

    `floor_at_smallest_unit` keeps a positive charge from rounding away to
    nothing: a model a thousand times cheaper than the reference still costs
    0.01, because a free AI call is a hole, not a bargain.
    """
    value = Decimal(amount).quantize(CREDIT_PLACES, rounding=ROUND_HALF_UP)
    if floor_at_smallest_unit and Decimal(amount) > 0 and value <= 0:
        return CREDIT_PLACES
    return value


class CreditBalance(models.Model):
    """Per-user credit balance.

    Credits are granted on account creation (free tier) and when extra packs are
    purchased; each billable operation decrements the balance by its cost.
    """
    id                = models.AutoField(primary_key=True)
    user              = models.OneToOneField(User, on_delete=models.CASCADE, related_name="credits")
    credits           = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('10.00'))
    stripe_payment_id = models.CharField(max_length=255, blank=True)
    cdate             = models.DateTimeField(auto_now_add=True)
    mdate             = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'credits_creditbalance'
        verbose_name = 'Credit balance'
        verbose_name_plural = 'Credit balances'

    def has_remaining_calls(self):
        return self.credits > 0

    def decrement(self, count=1):
        # Decimal throughout — `self.credits - float(x)` raises, and going via
        # float would drift a balance by fractions of a cent per debit.
        remaining = Decimal(self.credits) - Decimal(str(count))
        self.credits = quantize_credits(max(Decimal('0'), remaining))
        self.save(update_fields=['credits', 'mdate'])

    def add_credits(self, amount, payment_id=None):
        self.credits = quantize_credits(Decimal(self.credits) + Decimal(str(amount)))
        if payment_id:
            self.stripe_payment_id = payment_id
        self.save(update_fields=['credits', 'stripe_payment_id', 'mdate'])

    def __str__(self):
        return f"Credit balance for {self.user.email}: {self.credits} credit(s) remaining"


class CreditCost(models.Model):
    """How many credits a billable operation costs. Managed from the Django admin
    — one row per active operation code. ``operation`` is an opaque, domain-agnostic
    code the consuming app defines and seeds (generator seeds its own)."""
    operation = models.CharField(max_length=30, unique=True)
    credits   = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal('1.00'),
        help_text='Credits deducted per operation, before any per-model coefficient',
    )

    class Meta:
        db_table = 'credits_creditcost'
        ordering  = ['operation']
        verbose_name        = 'Credit cost'
        verbose_name_plural = 'Credit costs'

    def __str__(self):
        return f"{self.operation}: {self.credits} credit(s)"
