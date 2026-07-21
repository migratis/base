"""Subscription integration with the unified `stripe_payment` engine.

Registers, for the ``subscription`` purpose:

* a **checkout builder** — turns a plan choice into a ``mode='subscription'``
  Checkout Session (with a trial when the user is trial-eligible);
* a **grant handler** — materialises/activates the local ``Subscription`` when
  the Checkout completes, run once through the shared idempotent ledger;
* **lifecycle event handlers** — the invoice / subscription / customer / product
  webhooks the old ``/subscription/webhook`` used to own, now dispatched by the
  single ``/billing/webhook``.

Wired at app start from ``SubscriptionConfig.ready()``.
"""
from datetime import datetime

import requests
import stripe
from django.conf import settings
from django.core.files.base import ContentFile

from migratis.i18n.models import TranslationKey
from migratis.stripe_payment.plugins import BillingPlugin, register_plugin
from . import models

stripe.api_key = settings.STRIPE_SECRET_KEY


# --------------------------------------------------------------------------- #
# Checkout builder
# --------------------------------------------------------------------------- #
def build_subscription_checkout(request, user):
    """Assemble the Checkout kwargs for subscribing to a plan. Returns
    ``(kwargs, error)`` — error is a formatErrors-style dict on bad input."""
    from .views import hasTrial

    plan_id = request.POST.get('plan_id', request.GET.get('plan_id'))
    try:
        plan = models.Plan.objects.get(pk=int(plan_id), active=True)
    except (models.Plan.DoesNotExist, TypeError, ValueError):
        return None, {'plan': ['plan-not-exists']}

    subscription_data = {}
    if hasTrial(user):
        subscription_data['trial_period_days'] = 30

    kwargs = dict(
        mode='subscription',
        line_items=[{'price': plan.stripe_id, 'quantity': 1}],
        success_url=f'{settings.FRONTEND_URL}/subscribe?payment=success&session_id={{CHECKOUT_SESSION_ID}}',
        cancel_url=f'{settings.FRONTEND_URL}/subscribe?payment=cancelled',
        metadata={'plan_id': str(plan.id), 'life': '1' if plan.life else ''},
        subscription_data=subscription_data,
    )
    return kwargs, None


# --------------------------------------------------------------------------- #
# Grant + subscription upsert
# --------------------------------------------------------------------------- #
def _upsert_subscription_from_stripe(stripe_sub, fallback_user=None, plan_id=None):
    """Create-or-update the local Subscription from a Stripe subscription object.

    Order-independent: derives the user (via Customer) and plan (via price id)
    from Stripe so it works whether ``checkout.session.completed`` or
    ``customer.subscription.updated`` arrives first.
    """
    customer = models.Customer.objects.filter(
        stripe_id=stripe_sub.customer
    ).select_related('user').first()
    user = customer.user if customer else fallback_user
    if user is None:
        return None

    plan = None
    if plan_id:
        plan = models.Plan.objects.filter(pk=plan_id).first()
    if plan is None:
        try:
            price_id = stripe_sub['items']['data'][0]['price']['id']
            plan = models.Plan.objects.filter(stripe_id=price_id).first()
        except (KeyError, IndexError, TypeError):
            plan = None
    if plan is None:
        return None

    sub, _ = models.Subscription.objects.get_or_create(
        stripe_id=stripe_sub.id,
        defaults=dict(user=user, customer=customer, plan=plan, status='incomplete'),
    )

    if plan.life and getattr(stripe_sub, 'cancel_at', None):
        sub.access = True
        sub.status = 'infinite'
    else:
        sub.status = stripe_sub.status
        sub.access = stripe_sub.status in ('active', 'trialing')
        try:
            sub.end = datetime.fromtimestamp(
                stripe_sub['items']['data'][0]['current_period_end']
            )
        except (KeyError, IndexError, TypeError):
            pass

    if sub.customer is None and customer:
        sub.customer = customer
    sub.plan = plan
    sub.save()
    return sub


def grant_subscription(user, session, payment):
    """Activate the local Subscription once the Checkout completes. Idempotent
    via the ledger; the lifecycle events keep it in sync afterwards."""
    sub_id = session.get('subscription') if isinstance(session, dict) else getattr(session, 'subscription', None)
    if not sub_id:
        return
    stripe_sub = stripe.Subscription.retrieve(sub_id)
    _upsert_subscription_from_stripe(
        stripe_sub, fallback_user=user, plan_id=(payment.metadata or {}).get('plan_id')
    )


# --------------------------------------------------------------------------- #
# Lifecycle event handlers (ported from the old /subscription/webhook)
# --------------------------------------------------------------------------- #
def on_subscription_updated(event):
    obj = event['data']['object']
    stripe_sub = stripe.Subscription.retrieve(obj['id'])
    _upsert_subscription_from_stripe(stripe_sub)


def on_subscription_deleted(event):
    obj = event['data']['object']
    sub = models.Subscription.objects.filter(stripe_id=obj['id']).first()
    if sub:
        sub.access = False
        sub.status = "deleted"
        sub.save()


def on_invoice_created(event):
    data_object = event['data']['object']
    if models.Invoice.objects.filter(stripe_id=data_object['id']).exists():
        return
    customer = models.Customer.objects.filter(stripe_id=data_object['customer']).select_related('user').first()
    if not customer:
        return
    try:
        sub_id = data_object['parent']['subscription_details']['subscription']
    except (KeyError, TypeError):
        return
    subscription = models.Subscription.objects.filter(stripe_id=sub_id).select_related('plan', 'plan__label').first()
    if not subscription:
        return
    label_key = ''
    if subscription.plan and subscription.plan.label:
        label_key = subscription.plan.label.key
    invoice = models.Invoice(
        user=customer.user,
        customer=customer,
        purpose='subscription',
        reference=subscription.stripe_id or '',
        label_key=label_key,
        status=data_object['status'],
        stripe_id=data_object['id'],
        amount=data_object['amount_due'],
    )
    detailed_invoice = stripe.Invoice.retrieve(data_object['id'], expand=['total_tax_amounts.tax_rate'])
    if detailed_invoice.get('total_tax_amounts'):
        invoice.tax = detailed_invoice.total_tax_amounts[0].tax_rate.percentage
    invoice.save()


def on_invoice_payment_failed(event):
    data_object = event['data']['object']
    invoice = models.Invoice.objects.filter(stripe_id=data_object['id']).first()
    if invoice:
        invoice.status = data_object['status']
        invoice.save()


def on_invoice_payment_succeeded(event):
    data_object = event['data']['object']
    invoice = models.Invoice.objects.filter(stripe_id=data_object['id']).first()
    if not invoice:
        return
    invoice.status = data_object['status']
    invoice.save()

    try:
        sub_id = data_object['parent']['subscription_details']['subscription']
    except (KeyError, TypeError):
        return

    stripe_subscription = stripe.Subscription.retrieve(
        sub_id, expand=['pending_setup_intent.payment_method']
    )
    stripe_invoice = stripe.Invoice.retrieve(data_object['id'], expand=['payment_intent'])

    if stripe_invoice.get('payment_intent'):
        intent = stripe_invoice.payment_intent
    else:
        intent = stripe_subscription.pending_setup_intent

    if intent:
        if not intent.payment_method.customer:
            stripe.PaymentMethod.attach(intent.payment_method.id, customer=data_object['customer'])
        if not stripe_subscription.default_payment_method:
            stripe.Subscription.modify(
                sub_id,
                default_payment_method=intent.payment_method.id,
                payment_settings={'payment_method_types': ['card']},
            )
        customer = stripe.Customer.retrieve(data_object['customer'])
        if not customer.invoice_settings.default_payment_method:
            stripe.Customer.modify(
                data_object['customer'],
                invoice_settings={'default_payment_method': intent.payment_method.id},
            )

    subscription = models.Subscription.objects.filter(stripe_id=sub_id).select_related('plan').first()
    if not subscription:
        return
    item = stripe.SubscriptionItem.list(limit=1, subscription=subscription.stripe_id)
    if subscription.plan.stripe_id != item.data[0].price.id:
        plan = models.Plan.objects.filter(stripe_id=item.data[0].price.id).first()
        if plan:
            subscription.plan = plan
            subscription.save()
    if subscription.plan.life and data_object['amount_paid'] == data_object['amount_due'] and data_object['amount_due'] > 0:
        stripe.Subscription.modify(subscription.stripe_id, cancel_at_period_end=True)


def on_invoice_finalized(event):
    data_object = event['data']['object']
    invoice = models.Invoice.objects.filter(stripe_id=data_object['id']).first()
    if not invoice:
        return
    response = requests.get(data_object['invoice_pdf'])
    invoice.status = data_object['status']
    invoice.file.save(data_object['id'] + ".pdf", ContentFile(response.content))
    invoice.save()


def on_customer_deleted(event):
    data_object = event['data']['object']
    customer = models.Customer.objects.filter(stripe_id=data_object['id']).first()
    if not customer:
        return
    subscriptions = models.Subscription.objects.filter(user=customer.user)
    customer.delete()
    for subscription in subscriptions:
        subscription.delete()


def on_product_updated(event):
    data_object = event['data']['object']
    plan = models.Plan.objects.filter(product=data_object['id']).first()
    if plan:
        if plan.label.key == "subscription-life":
            plan.life = True
        plan.active = bool(data_object['active'])
        plan.save()
    else:
        label = TranslationKey.objects.get(key=data_object['name'])
        new_plan = models.Plan(product=data_object['id'], label=label, active=True)
        if label.key == "subscription-life":
            new_plan.life = True
        price = stripe.Price.retrieve(data_object['default_price'])
        new_plan.price = price.unit_amount / 100
        new_plan.stripe_id = data_object['default_price']
        new_plan.save()


def register():
    register_plugin(BillingPlugin(
        purpose='subscription',
        checkout_builder=build_subscription_checkout,
        grant_handler=grant_subscription,
        events={
            'customer.subscription.updated': on_subscription_updated,
            'customer.subscription.deleted': on_subscription_deleted,
            'invoice.created': on_invoice_created,
            'invoice.payment_failed': on_invoice_payment_failed,
            'invoice.payment_succeeded': on_invoice_payment_succeeded,
            'invoice.finalized': on_invoice_finalized,
            'customer.deleted': on_customer_deleted,
            'product.updated': on_product_updated,
        },
        label_key='subscription',
        module='subscription',
    ))
