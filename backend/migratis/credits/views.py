"""Credit API — balance, purchasable tiers, and per-operation costs.

Relocated from the generator app (was /generator/ai-usage*, /generator/ai/call-costs).
Buying credits still goes through the shared engine:
POST /billing/checkout?purpose=credits → GET /billing/checkout/verify.
"""
from django.conf import settings
from ninja import Router

from .models import CreditCost
from .services import get_or_create_balance, has_active_subscription

router = Router()


# NOTE on @check_access: these endpoints are intentionally NOT gated by
# @check_access(). Credits exist FOR users WITHOUT a subscription — the default
# entitlement provider denies exactly those users, so gating the credit balance /
# price list behind the entitlement they come here to buy would be a
# contradiction (the same reasoning that leaves /billing/checkout and the
# subscription plans/tax endpoints ungated). They still require authentication
# (the API default auth) and scope strictly to request.user.


@router.get('/balance')
def balance(request):
    """Current credit balance. `unlimited` is True when an active subscription
    covers usage — the frontend hides the counter / buy affordance in that case
    (a subscriber never spends credits)."""
    bal = get_or_create_balance(request.user)
    return {
        'credits':   bal.credits,
        'unlimited': has_active_subscription(request.user),
    }


@router.get('/tiers')
def tiers(request):
    """Available credit packs for purchase."""
    return [
        {
            'extra_amount': tier['extra_amount'],
            'price': tier['price'],
            'currency': settings.CREDITS_CURRENCY,
        }
        for tier in settings.CREDIT_TIERS
    ]


@router.get('/costs')
def costs(request):
    """Return the credit cost for each configured operation."""
    return {c.operation: c.credits for c in CreditCost.objects.all()}
