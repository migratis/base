"""Credit API — balance, purchasable tiers, and per-operation costs.

Relocated from the generator app (was /generator/ai-usage*, /generator/ai/call-costs).
Buying credits still goes through the shared engine:
POST /billing/checkout?purpose=credits → GET /billing/checkout/verify.
"""
from django.conf import settings
from ninja import Router

from migratis.subscription.decorators import check_access
from .models import CreditCost
from .services import get_or_create_balance, has_active_subscription

router = Router()


@router.get('/balance')
@check_access()
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
@check_access()
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
@check_access()
def costs(request):
    """Return the credit cost for each configured operation."""
    return {c.operation: c.credits for c in CreditCost.objects.all()}
