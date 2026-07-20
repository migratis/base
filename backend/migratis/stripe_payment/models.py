from django.db import models
from migratis.user.models import User


class Customer(models.Model):
    """The per-user Stripe customer identity — shared by every paying feature.

    Relocated here from the subscription app (Phase 5); the DB table name is
    preserved (``subscription_customer``) so no data moves.
    """
    user      = models.ForeignKey(User, on_delete=models.CASCADE)
    cdate     = models.DateTimeField(auto_now_add=True)
    mdate     = models.DateTimeField(auto_now=True)
    stripe_id = models.CharField(max_length=50)

    class Meta:
        db_table = 'subscription_customer'
        verbose_name_plural = "Customers"

    def __str__(self):
        return f"{self.user.email} {self.stripe_id}"


class StripePayment(models.Model):
    """Idempotent grant ledger.

    A paid Checkout Session is applied to the platform **exactly once**: the
    purpose handler runs only when this row is first created, guarded by the
    unique ``stripe_session_id``. Shared by the webhook and the redirect-return
    verify, so a redirect-before-webhook race or a Stripe webhook retry can
    never double-apply a payment (the old AI-credit bug).
    """
    id                = models.AutoField(primary_key=True)
    user              = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stripe_payments')
    purpose           = models.CharField(max_length=32)
    stripe_session_id = models.CharField(max_length=255, unique=True)
    amount            = models.DecimalField(default=0, max_digits=12, decimal_places=2)
    currency          = models.CharField(max_length=10, blank=True)
    status            = models.CharField(max_length=32, default='completed')
    metadata          = models.JSONField(default=dict, blank=True)
    cdate             = models.DateTimeField(auto_now_add=True)
    mdate             = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Stripe payments"

    def __str__(self):
        return f"{self.user.email} {self.purpose} {self.stripe_session_id}"


class ProcessedStripeEvent(models.Model):
    """Webhook-level idempotency log — every Stripe event id is processed once.

    Covers Stripe's automatic retries for *all* event types (lifecycle events
    that aren't one-off grants, e.g. ``customer.subscription.updated``). The
    grant ledger above additionally protects the redirect-return path, which is
    not a webhook event.
    """
    id              = models.AutoField(primary_key=True)
    stripe_event_id = models.CharField(max_length=255, unique=True)
    type            = models.CharField(max_length=64)
    cdate           = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Processed Stripe events"

    def __str__(self):
        return f"{self.type} {self.stripe_event_id}"


class Invoice(models.Model):
    """A Stripe invoice for any paying purpose.

    Generalized (Phase 5) so one-off AI-credit purchases produce invoices too,
    not just subscriptions: ``subscription``/``plan`` are now nullable and
    ``purpose`` distinguishes the kind. Subscription/Plan are referenced by
    string so this module keeps a one-way dependency on the subscription domain
    only through the app registry (no import cycle). Table name preserved
    (``subscription_invoice``) so no data moves.
    """
    user         = models.ForeignKey(User, on_delete=models.CASCADE)
    customer     = models.ForeignKey('stripe_payment.Customer', on_delete=models.DO_NOTHING, null=True)
    subscription = models.ForeignKey('subscription.Subscription', on_delete=models.CASCADE, null=True)
    plan         = models.ForeignKey('subscription.Plan', on_delete=models.DO_NOTHING, null=True)
    payment      = models.ForeignKey('stripe_payment.StripePayment', on_delete=models.SET_NULL, null=True, blank=True)
    purpose      = models.CharField(max_length=32, default='subscription')
    status       = models.CharField(max_length=20, default='draft')
    file         = models.FileField(upload_to='migratis/subscription/invoices', blank=True, null=True)
    stripe_id    = models.CharField(max_length=50)
    amount       = models.DecimalField(default=0, max_digits=99, decimal_places=2)
    tax          = models.DecimalField(default=0, max_digits=99, decimal_places=2)
    cdate        = models.DateTimeField(auto_now_add=True)
    mdate        = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscription_invoice'
        verbose_name_plural = "Invoices"

    def __str__(self):
        return f"{self.user.email} {self.status} {self.stripe_id}"
