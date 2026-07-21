"""Credit integration with the unified `stripe_payment` engine.

Registers, for the ``credits`` purpose:

* a **checkout builder** — turns a tier / custom-quantity request into a
  one-off (``mode='payment'``) Checkout Session;
* a **grant handler** — credits the user, run exactly once through the shared
  idempotent ledger (`stripe_payment.services.grant_for_session`).

Wired at app start from ``CreditsConfig.ready()``. The product line-item label
and the ``label_key`` (invoice / plugin display) are de-AI'd — a plain "Credits"
top-up (the ``credits`` i18n key), not "AI Calls" (P6).
"""
from django.conf import settings

from migratis.stripe_payment.plugins import BillingPlugin, register_plugin


def build_credits_checkout(request, user):
    """Assemble the Checkout kwargs for a credit top-up. Returns
    ``(kwargs, error)`` — error is a formatErrors-style dict on bad input."""
    tiers = settings.CREDIT_TIERS
    raw_index = request.POST.get('tier_index', request.GET.get('tier_index'))
    try:
        tier_index = int(raw_index)
        tier = tiers[tier_index]
    except (TypeError, ValueError, IndexError):
        return None, {'tier': ['invalid-tier']}

    extra_amount = tier['extra_amount']
    unit_price = float(tier['price'])

    is_custom_tier = tier_index == len(tiers) - 1
    raw_qty = request.POST.get('custom_quantity', request.GET.get('custom_quantity'))
    if is_custom_tier and raw_qty:
        try:
            custom_quantity = int(raw_qty)
        except (TypeError, ValueError):
            return None, {'quantity': ['invalid-tier']}
        if custom_quantity < tier['extra_amount']:
            # The client already enforces the minimum; this is the safety net.
            return None, {'quantity': ['invalid-tier']}
        extra_amount = custom_quantity
        rate_per_call = unit_price / tier['extra_amount']
        unit_price = extra_amount * rate_per_call

    kwargs = dict(
        mode='payment',
        line_items=[{
            'price_data': {
                'currency': settings.CREDITS_CURRENCY,
                'product_data': {
                    'name': f'Extra {extra_amount} Credits',
                    'description': f'Purchase {extra_amount} additional credits for Migratis',
                },
                'unit_amount': int(unit_price * 100),
            },
            'quantity': 1,
        }],
        success_url=f'{settings.FRONTEND_URL}/generator/application?payment=success&session_id={{CHECKOUT_SESSION_ID}}',
        cancel_url=f'{settings.FRONTEND_URL}/generator/application?payment=cancelled',
        metadata={'extra_amount': str(extra_amount), 'tier_index': str(tier_index)},
        invoice_creation={'enabled': True},
    )
    return kwargs, None


def grant_credits(user, session, payment):
    """Apply purchased credits. Called once per session by the idempotent ledger,
    so a plain add is safe (no re-check needed)."""
    from .services import get_or_create_balance

    extra = int((payment.metadata or {}).get('extra_amount') or 0)
    if extra <= 0:
        return
    balance = get_or_create_balance(user)
    balance.add_credits(extra, payment.stripe_session_id)


# --------------------------------------------------------------------------- #
# Credit invoices — Stripe issues an invoice for the one-off buy (invoice_creation
# above). These handlers record it locally, purpose='credits', so it shows up
# in the same invoices list as subscription invoices. They self-filter to
# non-subscription invoices (the subscription handlers take the rest).
# --------------------------------------------------------------------------- #
def _is_subscription_invoice(data_object):
    try:
        return bool(data_object['parent']['subscription_details']['subscription'])
    except (KeyError, TypeError):
        return False


def on_credit_invoice_created(event):
    from migratis.stripe_payment.models import Customer, Invoice

    data_object = event['data']['object']
    if _is_subscription_invoice(data_object):
        return
    if Invoice.objects.filter(stripe_id=data_object['id']).exists():
        return
    customer = Customer.objects.filter(
        stripe_id=data_object['customer']
    ).select_related('user').first()
    if not customer:
        return
    Invoice.objects.create(
        user=customer.user,
        customer=customer,
        purpose='credits',
        label_key='credits',
        status=data_object['status'],
        stripe_id=data_object['id'],
        amount=data_object.get('amount_due', 0),
    )


def on_credit_invoice_finalized(event):
    import requests
    from django.core.files.base import ContentFile
    from migratis.stripe_payment.models import Invoice

    data_object = event['data']['object']
    if _is_subscription_invoice(data_object):
        return
    invoice = Invoice.objects.filter(stripe_id=data_object['id'], purpose='credits').first()
    if not invoice:
        return
    invoice.status = data_object['status']
    if data_object.get('invoice_pdf'):
        response = requests.get(data_object['invoice_pdf'])
        invoice.file.save(data_object['id'] + ".pdf", ContentFile(response.content))
    invoice.save()


def on_credit_invoice_paid(event):
    from migratis.stripe_payment.models import Invoice

    data_object = event['data']['object']
    if _is_subscription_invoice(data_object):
        return
    invoice = Invoice.objects.filter(stripe_id=data_object['id'], purpose='credits').first()
    if invoice:
        invoice.status = data_object['status']
        invoice.save()


def register():
    register_plugin(BillingPlugin(
        purpose='credits',
        checkout_builder=build_credits_checkout,
        grant_handler=grant_credits,
        events={
            'invoice.created': on_credit_invoice_created,
            'invoice.finalized': on_credit_invoice_finalized,
            'invoice.payment_succeeded': on_credit_invoice_paid,
        },
        label_key='credits',
        # Generated-app module this plugin backs (decision D6). The generator's
        # 'credits' Application-module lands in P4b; declaring it now means the
        # picker will derive it from here with no further edit.
        module='credits',
    ))
