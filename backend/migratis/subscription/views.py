from django.http import JsonResponse, FileResponse
from django.core.exceptions import ValidationError
from django.conf import settings
from ninja import Router, Form
from . import models, schemas
from migratis.api.functions import formatErrors
from typing import List
import stripe
from migratis.subscription.decorators import check_access
from migratis.stripe_payment.services import (
    ensure_customer as _ensure_customer,
    stripe_error_dict as _stripe_error_dict,
    sync_invoices as _sync_invoices,
)

stripe.api_key = settings.STRIPE_SECRET_KEY

router = Router()

def hasTrial(user):
    # Trial is optional (settings.SUBSCRIPTION_TRIAL, default True). When off,
    # nobody is trial-eligible — the subscription checkout builder omits the
    # Checkout trial period, and user.trial is False everywhere.
    if not getattr(settings, 'SUBSCRIPTION_TRIAL', True):
        return False
    return False if models.Subscription.objects.select_related('user').filter(
        user=user.id,
        status__in=['active', 'canceled', 'deleted', 'trialing', 'past_due']
    ).count() > 0 else True

def hasAccess(user):
    return True if models.Subscription.objects.select_related('user').get(
        user=user.id, 
        access=True
    ) else False

def doUnsubscribe(userId):
    subscription = models.Subscription.objects.select_related('user').get(
        user=userId, 
        access=True
    )
    response = stripe.Subscription.modify(
        subscription.stripe_id,
        cancel_at_period_end=True
    )
    subscription.cancelled = True
    subscription.save()
    return response

# saveCustomer / stripeErrorDict now live in the shared stripe_payment engine
# (services.ensure_customer / services.stripe_error_dict). These thin aliases keep
# the existing callers in user/views.py (register/update/invitation) and getTax
# working unchanged, with a single implementation of the customer round-trip.
def saveCustomer(user):
    return _ensure_customer(user)


def stripeErrorDict(error):
    return _stripe_error_dict(error)


@router.get('/plans', response=List[schemas.PlanSchema], auth=None)
def getPlanList(request):
    try:
        plans = models.Plan.objects.filter(active=True)
    except(TypeError, ValueError, OverflowError, models.Plan.DoesNotExist):
        plans = None
    if plans is not None:
        return plans
    return JsonResponse({"detail": formatErrors({"plan": ["plan-not-exists"]})}, status=422)

@router.get('/unsubscribe')
@check_access()  
def unsubscribe(request):
    userId = request.user.id
    try:
        doUnsubscribe(userId)
    except models.Subscription.DoesNotExist:
        return JsonResponse({"detail": formatErrors({"subscription": ["subscription-not-exists"]})}, status=422)
    
    return JsonResponse({"success": "unsubscribe-successful"})

@router.get('/resubscribe')
@check_access()  
def resubscribe(request):
    userId = request.user.id
    try: 
        subscription = models.Subscription.objects.select_related(
            'user',
            'customer'  
        ).get(user=userId, access=True)
        stripe.Subscription.modify(
            subscription.stripe_id,
            cancel_at_period_end=False
        )
        subscription.cancelled = False
        subscription.save()
    except models.Subscription.DoesNotExist:
        return JsonResponse({"detail": formatErrors({"subscription": ["subscription-not-exists"]})}, status=422)
    
    return JsonResponse({"success": "reactivate-successful"})

@router.get('/invoices', response=List[schemas.InvoiceSchema])
def invoices(request):
    userId = request.user.id
    # Pull any invoices Stripe has but we don't (missed/undelivered webhooks —
    # always the case on a localhost dev box). Best-effort: a Stripe hiccup must
    # not blank the list, so we still return whatever is already stored.
    try:
        _sync_invoices(request.user)
    except Exception:
        pass
    invoices = models.Invoice.objects.select_related(
        'user',
        'customer',
    ).filter(user=userId).order_by('-mdate')
    return invoices

@router.get('/invoice/download/{id}', response=List[schemas.InvoiceSchema])
def download(request, id: int):
    userId = request.user.id
    try:
        invoice = models.Invoice.objects.select_related(
            'user',
            'customer',
        ).get(pk=id, user=userId)
    except models.Invoice.DoesNotExist:
        return JsonResponse({"detail": formatErrors({"invoice": ["invoice-not-exists"]})}, status=422)
    #path = '{}/{}'.format(settings.BASE_DIR, invoice.file.name)
    #with open(invoice.file.path, "rb") as f:
    #    file = f.read()
    
    response =  FileResponse(invoice.file.open('rb'))
    response['Content-Type'] = 'application/pdf'
    response['Content-Disposition'] = 'attachment;'
    return response

@router.get('/tax/{id}')
def getTax(request, id: str):
    try:
        plan = models.Plan.objects.get(pk=id)
    except models.Plan.DoesNotExist:
        return JsonResponse({'error': "no-plan-available"})
    user = models.User.objects.get(pk=request.user.id)
    try:
        customer = models.Customer.objects.select_related('user').get(user=user)
    except models.Customer.DoesNotExist:
        # A user who registered while the subscription module was off has no
        # Stripe customer yet (ensure_customer short-circuits under
        # NO_SUBSCRIPTION). Materialise it here so the tax preview can be
        # computed instead of dead-ending on "no-customer".
        saved, error = saveCustomer(user)
        if not saved:
            return JsonResponse({"detail": formatErrors(stripeErrorDict(error))}, status=422)
        try:
            customer = models.Customer.objects.select_related('user').get(user=user)
        except models.Customer.DoesNotExist:
            return JsonResponse({'error': "no-customer"})
    price = stripe.Price.retrieve(plan.stripe_id)
    
    if price.type == 'one_time':
        invoice = stripe.Invoice.create_preview(
            customer=customer,
            invoice_items=[{
                "price": plan.stripe_id,
                "quantity": 1,
            }],
            automatic_tax={"enabled": True},
        ) 
    else: 
        invoice = stripe.Invoice.create_preview(
            customer=customer,
            subscription_details={
                "items":[{
                    "price": plan.stripe_id,
                    "quantity": 1,
                }],
            },
            automatic_tax={"enabled": True},
        )
    
    amount = 0
    rate = 0
    if invoice.get('total_taxes'):
        amount = invoice.total_taxes[0].amount
        rate_id = invoice.total_taxes[0].tax_rate_details.tax_rate
        rate = stripe.TaxRate.retrieve(rate_id)
    return JsonResponse({'tax': { 'amount': amount, 'rate': rate.percentage }})


@router.post('/change') 
@check_access()      
def changePlan(request, id: Form[int]):
    try:
        user = models.User.objects.get(pk=request.user.id)
        try:
            plan = models.Plan.objects.get(
                pk=id,
                active=True
            )
        except models.Plan.DoesNotExist:
            return JsonResponse({"detail": formatErrors({'plan': 'unknown-plan'})}, status=422)
        try:
            subscription = models.Subscription.objects.select_related(
                'user', 
                'plan'
            ).get(
                user=user,
                status__in=['trialing', 'active', 'infinite'],
                cancelled=False,
            )
            item = stripe.SubscriptionItem.list(
                limit=1,
                subscription=subscription.stripe_id
            )
            stripe.SubscriptionItem.modify(
                item.data[0].id,
                price=plan.stripe_id
            )                       
            if plan.price > subscription.plan.price:
                return JsonResponse({"detail": [{
                    "success": ["subscription-successfully-changed-proceed-to-payment"],
                    'need-payment': True,
                }]})
            else:
                return JsonResponse({"detail": [{
                    "success": ["subscription-successfully-changed"],
                    'need-payment': False
                }]})            
        except models.Subscription.DoesNotExist:
            return JsonResponse({"detail": formatErrors({'subscription': 'existing-subscription-not-found'})}, status=422)
    except ValidationError as e:
        return JsonResponse({"detail": formatErrors(e.message_dict)}, status=422)
