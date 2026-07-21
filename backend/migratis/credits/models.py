"""Credit models — a standalone, de-AI'd billing feature.

Relocated from ``generator`` (was ``UserAIUsage`` / ``AICallCost``). Physical
tables are renamed in place (``credits_creditbalance`` / ``credits_creditcost``)
so **no rows move**. The field stays ``credits`` (decision D1); the price table
is keyed on ``call_type`` for now (decoupled to an opaque ``operation`` in P3).

This module imports nothing from ``generator`` — credits is installable on its
own; ``generator`` is a *consumer* of credits, inverting the old coupling.
"""
from django.db import models

from migratis.user.models import User


class CreditBalance(models.Model):
    """Per-user credit balance.

    Credits are granted on account creation (free tier) and when extra packs are
    purchased; each billable operation decrements the balance by its cost.
    """
    id                = models.AutoField(primary_key=True)
    user              = models.OneToOneField(User, on_delete=models.CASCADE, related_name="credits")
    credits           = models.IntegerField(default=10)
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
        self.credits = max(0, self.credits - count)
        self.save(update_fields=['credits', 'mdate'])

    def add_credits(self, amount, payment_id=None):
        self.credits += amount
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
    credits   = models.PositiveIntegerField(default=1, help_text='Number of credits deducted per operation')

    class Meta:
        db_table = 'credits_creditcost'
        ordering  = ['operation']
        verbose_name        = 'Credit cost'
        verbose_name_plural = 'Credit costs'

    def __str__(self):
        return f"{self.operation}: {self.credits} credit(s)"
