from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ninja import Router
import stripe

from migratis.api.functions import formatErrors
from . import registry
from .services import (
    create_checkout_session,
    grant_for_session,
    process_event,
    stripe_error_dict,
)

stripe.api_key = settings.STRIPE_SECRET_KEY

router = Router()


# NOTE on @check_access: the payment-initiation endpoints below are intentionally
# NOT gated by @check_access(). The default entitlement provider denies users
# without an active subscription — i.e. exactly the users who come here to buy a
# subscription or top-up credits. Gating payment behind the entitlement it grants
# would be a contradiction, which is why subscription's own plans/tax endpoints
# are ungated too. These endpoints require authentication (the API default auth)
# and every builder/handler scopes strictly to request.user.


@router.post('/checkout')
def checkout(request, purpose: str):
    """Unified Checkout entry point. `purpose` selects the registered builder
    (e.g. 'credits', 'subscription'), which assembles the line items; the
    shared service attaches the Customer and stamps routing metadata."""
    builder = registry.get_checkout_builder(purpose)
    if builder is None:
        return JsonResponse(
            {'detail': formatErrors({'purpose': ['invalid-purpose']})}, status=422
        )

    kwargs, error = builder(request, request.user)
    if error:
        return JsonResponse({'detail': formatErrors(error)}, status=422)

    session, stripe_err = create_checkout_session(
        request.user, purpose=purpose, **kwargs
    )
    if stripe_err is not None:
        return JsonResponse(
            {'detail': formatErrors(stripe_error_dict(stripe_err))}, status=422
        )
    return JsonResponse({'checkout_url': session.url})


@router.get('/checkout/verify')
def verify(request, session_id: str = None):
    """Called when the user returns from Checkout. Retrieves the session,
    verifies it belongs to this user, and applies the grant idempotently (the
    webhook may or may not have arrived yet). The frontend then refreshes its
    own state (credit balance / subscription)."""
    if not session_id:
        return JsonResponse({'success': False})
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe._error.StripeError:
        return JsonResponse({'success': False})

    metadata = session.get('metadata') or {}
    if str(metadata.get('user_id')) != str(request.user.id):
        # Never apply someone else's session to the caller.
        return JsonResponse({'success': False})

    applied, payment = grant_for_session(session)
    return JsonResponse({
        'success': bool(applied or payment is not None),
        'purpose': metadata.get('purpose'),
    })


@router.post('/webhook', auth=None)
@csrf_exempt
def webhook(request):
    """Single Stripe webhook for the whole platform (credits + subscription).

    Verifies the signature, then dedups on the Stripe event id and dispatches to
    the registered handlers. A bad/missing signature is a hard 400 (Stripe
    retries); a handler failure is a 500 (Stripe retries) after the event row is
    rolled back, so processing is exactly-once and self-healing.
    """
    sig_header = request.headers.get('Stripe-Signature', '')
    try:
        event = stripe.Webhook.construct_event(
            request.body, sig_header, settings.STRIPE_WEBHOOK_SECRET_KEY
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    try:
        process_event(event)
    except Exception:
        return HttpResponse(status=500)
    return HttpResponse(status=200)
