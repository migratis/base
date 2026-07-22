"""The unified Stripe billing engine.

One customer helper, one Checkout builder, one idempotent grant, one webhook
dispatcher — shared by every paying feature (subscription, AI credits, …).
Feature-specific logic lives in that feature's registered handlers (registry.py).
"""
import uuid

import stripe
from django.conf import settings
from django.db import transaction

from . import registry
from .models import Customer, ProcessedStripeEvent, StripePayment

stripe.api_key = settings.STRIPE_SECRET_KEY


def _customer_model():
    """The Customer model now lives in this app (relocated in Phase 5)."""
    return Customer


# --------------------------------------------------------------------------- #
# Customer
# --------------------------------------------------------------------------- #
def stripe_error_dict(error):
    """Map a Stripe error to the ``formatErrors()`` dict the API answers with.

    An ``InvalidRequestError`` is only about the tax number when Stripe points
    at a tax field (``error.param`` like ``tax_id``/``tax_id_data``) — the one
    free-form value the registration round-trip forwards. Any other invalid
    request is a platform/config problem, not the user's tax number: e.g. a
    ``Plan`` whose ``stripe_id`` isn't a live Price (a live/test mode mismatch →
    "No such price", ``param='line_items[0][price]'``), or an address rejected
    by automatic tax. Blaming the tax field there is a lie that misdirects every
    debugger — report the config failure truthfully instead. Anything that isn't
    an invalid request is the service itself failing.
    """
    if isinstance(error, stripe._error.InvalidRequestError):
        param = getattr(error, "param", "") or ""
        if "tax" in param:
            return {"taxnumber": ["taxnumber-invalid"]}
        return {"stripe": ["payment-config-error"]}
    return {"stripe": ["payment-service-unavailable"]}


def ensure_customer(user):
    """Create-if-missing / refresh-if-present the Stripe customer for ``user``.

    Honors ``NO_SUBSCRIPTION`` (no Stripe round-trip). Returns ``(saved, error)``
    — the same contract the whole codebase already expects from the old
    ``subscription.saveCustomer`` (which now delegates here).
    """
    if settings.NO_SUBSCRIPTION:
        return True, None

    Customer = _customer_model()
    from migratis.subscription.models import TAX_ID_TYPE

    try:
        try:
            customer = Customer.objects.select_related('user').get(user=user)
            stripe.Customer.modify(
                customer.stripe_id,
                email=user.email,
                address={
                    "city": user.city,
                    "country": (user.country.code).upper(),
                    "line1": user.address,
                    "postal_code": user.zipcode,
                },
                name=user.company if user.company else user.first_name + " " + user.last_name,
                preferred_locales=[user.language],
                invoice_settings={
                    "custom_fields": [{
                        "name": "taxnumber",
                        "value": user.taxnumber,
                    }]
                } if user.taxnumber else {},
                expand=["tax"],
                idempotency_key=str(uuid.uuid4()),
            )
        except Customer.DoesNotExist:
            customer = stripe.Customer.create(
                address={
                    "city": user.city,
                    "country": user.country.code,
                    "line1": user.address,
                    "postal_code": user.zipcode,
                },
                email=user.email,
                name=user.company if user.company else user.first_name + " " + user.last_name,
                preferred_locales=[user.language],
                invoice_settings={
                    "custom_fields": [{
                        "name": "taxnumber",
                        "value": user.taxnumber,
                    }]
                } if user.taxnumber else {},
                tax_id_data=[
                    {"type": TAX_ID_TYPE[(user.country.code).upper()], "value": user.taxnumber}
                ] if user.taxnumber else [],
                expand=["tax"],
                idempotency_key=str(uuid.uuid4()),
            )
            Customer.objects.create(user=user, stripe_id=customer.id)
    except stripe._error.StripeError as e:
        return False, e
    return True, None


def _customer_id(user):
    Customer = _customer_model()
    try:
        return Customer.objects.get(user=user).stripe_id
    except Customer.DoesNotExist:
        return None


# --------------------------------------------------------------------------- #
# Invoice back-fill
# --------------------------------------------------------------------------- #
def sync_invoices(user):
    """Materialise any of the user's Stripe invoices that aren't local yet.

    Invoices are normally created by the ``invoice.*`` webhooks, but those never
    reach a localhost dev box (no public URL) and can be missed/late in prod
    too. This pulls the customer's finalised invoices straight from Stripe and
    replays each missing one through the **already-registered** ``invoice.created``
    + ``invoice.finalized`` handlers — so the exact same, tested mapping runs
    (subscription vs credits self-selects via each handler's own filter) and the
    PDF is downloaded, with no logic duplicated here and no import into any
    feature app. Idempotent: the handlers skip invoices already stored.
    """
    if settings.NO_SUBSCRIPTION:
        return
    customer_id = _customer_id(user)
    if not customer_id:
        return

    from .models import Invoice as InvoiceModel

    existing = set(
        InvoiceModel.objects.filter(user=user).values_list('stripe_id', flat=True)
    )
    try:
        stripe_invoices = stripe.Invoice.list(customer=customer_id, limit=100)
    except stripe._error.StripeError:
        return

    for inv in stripe_invoices.auto_paging_iter():
        data = inv.to_dict() if hasattr(inv, 'to_dict') else dict(inv)
        # Only finalised invoices have a PDF and a settled status worth showing.
        if data.get('status') not in ('paid', 'open', 'uncollectible'):
            continue
        if data.get('id') in existing:
            continue
        event = {'data': {'object': data}}
        for handler in registry.get_event_handlers('invoice.created'):
            handler(event)
        for handler in registry.get_event_handlers('invoice.finalized'):
            handler(event)


# --------------------------------------------------------------------------- #
# Checkout
# --------------------------------------------------------------------------- #
def create_checkout_session(user, *, mode, purpose, line_items,
                            success_url, cancel_url, metadata=None,
                            subscription_data=None, invoice_creation=None):
    """Create a hosted Checkout Session for any purpose.

    ``mode='payment'`` for one-off buys (AI credits), ``mode='subscription'``
    for plans. Always attaches the platform ``Customer`` (so one-off buys get
    tax + invoices too) and stamps ``purpose``/``user_id`` metadata that the
    webhook and redirect-return use to route the grant. Returns
    ``(session, None)`` or ``(None, error)``.
    """
    saved, error = ensure_customer(user)
    if not saved:
        return None, error

    meta = dict(metadata or {})
    meta['purpose'] = purpose
    meta['user_id'] = str(user.id)

    params = dict(
        mode=mode,
        line_items=line_items,
        metadata=meta,
        success_url=success_url,
        cancel_url=cancel_url,
    )

    customer_id = _customer_id(user)
    if customer_id:
        params['customer'] = customer_id
        params['automatic_tax'] = {"enabled": True}
        # Automatic tax needs a tax-determinable customer address. Many users
        # (e.g. non-professionals, who aren't required to give a full billing
        # address at registration) have none stored, which would make Stripe
        # reject the session with an InvalidRequestError and block the payment.
        # Have Checkout collect the address and persist it back onto the
        # Customer so the transaction goes through regardless of what was
        # captured up front.
        params['billing_address_collection'] = 'required'
        params['customer_update'] = {'address': 'auto'}

    if mode == 'payment':
        # Carry the routing metadata onto the PaymentIntent too, for parity with
        # any dashboards / reconciliation keyed off the intent.
        params['payment_intent_data'] = {'metadata': meta}
        if invoice_creation is not None:
            # Make Stripe generate a proper invoice (+ PDF) for the one-off buy,
            # so credit purchases are invoiced just like subscriptions.
            params['invoice_creation'] = invoice_creation
    elif mode == 'subscription':
        sub_data = dict(subscription_data or {})
        sub_data.setdefault('metadata', {}).update(meta)
        params['subscription_data'] = sub_data

    try:
        session = stripe.checkout.Session.create(
            idempotency_key=str(uuid.uuid4()), **params
        )
    except stripe._error.StripeError as e:
        return None, e
    return session, None


# --------------------------------------------------------------------------- #
# Idempotent grant + webhook dispatch
# --------------------------------------------------------------------------- #
def _get(obj, key, default=None):
    """Read a key off a Stripe object or a plain dict interchangeably."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def grant_for_session(session):
    """Idempotently apply a paid Checkout Session.

    Runs the registered purpose handler exactly once per session id, guarded by
    ``StripePayment``'s unique ``stripe_session_id`` and a row lock on the user
    (so the webhook and the redirect-return can never both apply). Returns
    ``(applied, payment)``; ``applied`` is False when the session isn't paid,
    has no routable metadata, or was already applied.
    """
    session_id = _get(session, 'id')
    payment_status = _get(session, 'payment_status')
    # Paid one-off, or a trialing subscription that needs no immediate payment.
    if payment_status not in ('paid', 'no_payment_required'):
        return False, None

    metadata = _get(session, 'metadata') or {}
    # A live webhook delivers metadata as a Stripe `StripeObject`, on which
    # `dict(...)` raises — normalise to a plain dict (unit tests pass a dict).
    if hasattr(metadata, 'to_dict'):
        metadata = metadata.to_dict()
    purpose = metadata.get('purpose')
    user_id = metadata.get('user_id')
    if not purpose or not user_id:
        return False, None

    handler = registry.get_purpose_handler(purpose)
    if handler is None:
        return False, None

    from migratis.user.models import User

    amount_total = _get(session, 'amount_total') or 0
    currency = _get(session, 'currency') or ''

    with transaction.atomic():
        # Lock the user row first so all grants for this user serialise; the
        # unique constraint on stripe_session_id is the cross-user backstop.
        user = User.objects.select_for_update().get(id=user_id)
        payment, created = StripePayment.objects.get_or_create(
            stripe_session_id=session_id,
            defaults=dict(
                user=user,
                purpose=purpose,
                amount=amount_total / 100.0,
                currency=currency,
                status='completed',
                metadata=dict(metadata),
            ),
        )
        if not created:
            return False, payment
        handler(user, session, payment)
    return True, payment


def process_event(event):
    """Dispatch a *verified* Stripe event through the shared idempotency layer.

    Deduplicates on the event id (Stripe retries), grants for completed Checkout
    Sessions, and fans out lifecycle events to registered event handlers. Any
    handler exception rolls back the ProcessedStripeEvent row so Stripe retries.
    """
    event_id = _get(event, 'id')
    event_type = _get(event, 'type')

    with transaction.atomic():
        _, created = ProcessedStripeEvent.objects.get_or_create(
            stripe_event_id=event_id, defaults={'type': event_type or ''}
        )
        if not created:
            return  # already processed

        data = _get(event, 'data') or {}
        obj = _get(data, 'object')

        if event_type == 'checkout.session.completed' and obj is not None:
            grant_for_session(obj)

        for handler in registry.get_event_handlers(event_type):
            handler(event)
