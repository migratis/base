from django.http import JsonResponse, FileResponse
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from ninja import Router, Form
from . import models, schemas
from datetime import datetime
from dateutil.relativedelta import relativedelta
from migratis.api.functions import formatErrors
from typing import List
from pprint import pprint
import stripe
import uuid
import requests
from migratis.i18n.models import TranslationKey
from migratis.subscription.decorators import check_access

stripe.api_key = settings.STRIPE_SECRET_KEY

router = Router()

def hasTrial(user):
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

def saveCustomer(user):
    try:
        try:
            customer = models.Customer.objects.select_related('user').get(user=user)
            stripe.Customer.modify(
                customer.stripe_id,
                email=user.email,
                address={
                    "city": user.city,
                    "country": (user.country.code).upper(),
                    "line1": user.address,
                    "postal_code": user.zipcode
                },
                name=user.company if user.company else user.first_name + " " + user.last_name,
                preferred_locales=[user.language],
                invoice_settings={
                    "custom_fields": [{
                        "name": "taxnumber",
                        "value": user.taxnumber
                    }]
                } if user.taxnumber else {},
                expand=["tax"],
                idempotency_key=str(uuid.uuid4()),
                #test_clock="clock_1P4KXWAXmadDuP9DaUdW6fZ2"
            )      
        except models.Customer.DoesNotExist:
            customer = stripe.Customer.create(
                address={
                    "city": user.city,
                    "country": user.country.code,
                    "line1": user.address,
                    "postal_code": user.zipcode
                },
                email=user.email,
                name=user.company if user.company else user.first_name + " " + user.last_name,
                preferred_locales=[user.language],
                invoice_settings={
                    "custom_fields": [{
                        "name": "taxnumber",
                        "value": user.taxnumber
                    }]
                } if user.taxnumber else {},
                tax_id_data=[
                    {"type": models.TAX_ID_TYPE[(user.country.code).upper()], "value": user.taxnumber}
                ] if user.taxnumber else [],
                expand=["tax"],
                idempotency_key=str(uuid.uuid4()),            
                #test_clock="clock_1P4KXWAXmadDuP9DaUdW6fZ2"
            ) 
            customerId = customer.id
            new_customer = models.Customer()
            new_customer.user = user
            new_customer.stripe_id = customerId
            new_customer.save()
    except stripe._error.InvalidRequestError as e:
        error = e
        return False, e
    return True, None

@router.get('/payment/{plan_id}')
def createPayment(request, plan_id: int):
    intent = False
    userId = request.user.id        
    try:
        user = models.User.objects.get(pk=userId)
        trial = hasTrial(user)
    except models.User.DoesNotExist as e:
        return JsonResponse({"detail": formatErrors(e.message_dict)}, status=422)
    try:
        plan = models.Plan.objects.get(pk=plan_id)
    except models.Plan.DoesNotExist as e:
        return JsonResponse({"detail": formatErrors(e.message_dict)}, status=422) 
    try:
        customer = models.Customer.objects.select_related('user').get(user=userId)
        customerId = customer.stripe_id
    except models.Customer.DoesNotExist:
        try:
            stripe_customer = stripe.Customer.create(
                address={
                    "city": user.city,
                    "country": user.country.code,
                    "line1": user.address,
                    "postal_code": user.zipcode
                },
                email=user.email,
                name=user.company if user.company else user.first_name + " " + user.last_name,
                preferred_locales=[user.language],
                invoice_settings={
                    "custom_fields": [{
                        "name": "taxnumber",
                        "value": user.taxnumber
                    }]
                } if user.taxnumber else {},
                tax_id_data=[
                    {"type": models.TAX_ID_TYPE[(user.country.code).upper()], "value": user.taxnumber}
                ] if user.taxnumber else [],
                expand=["tax"],
                idempotency_key=str(uuid.uuid4()),
                #test_clock="clock_1P4KXWAXmadDuP9DaUdW6fZ2"
            )  
            customerId = stripe_customer.id
            customer = models.Customer()
            customer.user = user
            customer.stripe_id = customerId
            try:
                customer.save()
            except ValidationError as e:
                if (customer.id is not None): 
                    customer.delete()
                return JsonResponse({"detail": formatErrors(e.message_dict)}, status=422)
        except stripe.error.InvalidRequestError as e:
            if e.code == "tax_id_invalid":
                return JsonResponse({"detail": formatErrors({"taxnumber": ["taxnumber-refused"]})}, status=422)
            else:
                return JsonResponse({"detail": [e.message]}, status=422) 
    subscription = models.Subscription.objects.select_related(
        'user', 
        'customer'
    ).filter(
        user=userId, 
        status__in=['incomplete', 'past_due']
    ).order_by("-cdate").first()
    if not subscription:
        if trial:
            trialEndDate = datetime.now() + relativedelta(months=1)
            stripe_subscription = stripe.Subscription.create(
                customer=customerId,
                payment_behavior="default_incomplete",            
                items=[
                    {"price": plan.stripe_id},
                ],
                metadata = {"life": plan.life},
                expand=['pending_setup_intent'],
                trial_end=int(str(trialEndDate.timestamp())[0:10]),
                automatic_tax={"enabled": True},
                idempotency_key=str(uuid.uuid4()),
            )
            pprint(stripe_subscription)
            secret = stripe_subscription.pending_setup_intent.client_secret
        else:
            stripe_subscription = stripe.Subscription.create(
                customer=customerId,
                payment_behavior="default_incomplete",            
                items=[
                    {"price": plan.stripe_id},
                ],
                metadata = {"life": plan.life},              
                expand=['latest_invoice.confirmation_secret'],
                automatic_tax={"enabled": True},
                idempotency_key=str(uuid.uuid4()),
            )
            secret = stripe_subscription.latest_invoice.confirmation_secret.client_secret
        subscriptionId = stripe_subscription.id 
        new_subscription = models.Subscription()
        new_subscription.user = user
        new_subscription.customer = customer
        new_subscription.plan = plan
        new_subscription.stripe_id = subscriptionId
        try:
            new_subscription.save()
        except ValidationError as e:
            if (new_subscription.id is not None): 
                new_subscription.delete()
            return JsonResponse({"detail": formatErrors(e.message_dict)}, status=422)
        return JsonResponse({'clientSecret': secret})
    else:
        if trial:
            stripe_subscription = stripe.Subscription.retrieve(
                subscription.stripe_id,
                expand=['pending_setup_intent']
            )
            secret = stripe_subscription.pending_setup_intent.client_secret
        else:
            stripe_subscription = stripe.Subscription.retrieve(
                subscription.stripe_id,
                expand=['latest_invoice.confirmation_secret']
            )
            secret = stripe_subscription.latest_invoice.confirmation_secret.client_secret
        if not secret and stripe_subscription.status in ["trialing", "active"]:
            subscription.access = True
            subscription.save()
            return JsonResponse({'paid': True})
        else:                  
            return JsonResponse({'clientSecret': secret})
        
@router.get('/plans', response=List[schemas.PlanSchema], auth=None)
def getPlanList(request):
    try:
        plans = models.Plan.objects.filter(active=True)
    except(TypeError, ValueError, OverflowError, models.Plan.DoesNotExist):
        plans = None
    if plans is not None:
        return plans
    return JsonResponse({"detail": formatErrors({"plan": ["plan-not-exists"]})}, status=422)

@router.post('/webhook', auth=None)
@csrf_exempt
def stripeWebhook(request):
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET_KEY
    signature = request.headers['Stripe-Signature']
    try:
        event = stripe.Webhook.construct_event(
            payload=request.body, sig_header=signature, secret=webhook_secret
        )
        data = event.data
    except Exception as e:
        return JsonResponse({'status': 'error', 'msg': e.message})
    
    event_type = event.type
    data_object = data.object 
    if event_type == 'invoice.created':        
        try:
            invoice_exists = models.Invoice.objects.select_related(
                'user',
                'customer',
                'subscription'    
            ).get(stripe_id=data_object.id)
            if invoice_exists:
                return JsonResponse({'Invoice already exists': data_object.id}, status=422)   
        except models.Invoice.DoesNotExist:
            pass
        try:  
            customer = models.Customer.objects.select_related('user').get(stripe_id=data_object.customer)
        except models.Customer.DoesNotExist:
            return JsonResponse({'no such customer': data_object.customer}, status=422)
        try: 
            subscription = models.Subscription.objects.select_related(
                'user',
                'customer'
            ).get(stripe_id=data_object.parent.subscription_details.subscription)
        except models.Subscription.DoesNotExist:
            return JsonResponse({'no such subscription': data_object.parent.subscription_details.subscription}, status=422)    
        invoice = models.Invoice()
        invoice.user = customer.user
        invoice.subscription = subscription
        invoice.customer = customer
        invoice.plan = subscription.plan
        invoice.status = data_object.status
        invoice.stripe_id = data_object.id
        invoice.amount = data_object.amount_due
        detailed_invoice = stripe.Invoice.retrieve(data_object.id, expand=['total_tax_amounts.tax_rate'])
        if detailed_invoice.get('total_tax_amounts'):            
            invoice.tax = detailed_invoice.total_tax_amounts[0].tax_rate.percentage
        invoice.save()
    elif event_type == 'invoice.payment_failed':
        try:
            invoice = models.Invoice.objects.select_related(
                'user',
                'customer',
                'subscription'    
            ).get(stripe_id=data_object.id)
            invoice.status = data_object.status 
            invoice.save()
        except models.Invoice.DoesNotExist:
            return JsonResponse({'no such invoice': data_object.id}, status=422)
    elif event_type == 'invoice.payment_succeeded':
        try:
            invoice = models.Invoice.objects.select_related(
                'user',
                'customer',
                'subscription'    
            ).get(stripe_id=data_object.id)
            invoice.status = data_object.status            
            invoice.save()
            stripe_subscription = stripe.Subscription.retrieve(
                data_object.parent.subscription_details.subscription,
                expand=['pending_setup_intent.payment_method']
            )
            stripe_invoice = stripe.Invoice.retrieve(
                data_object.id,
                expand=['payment_intent']
            )
            
            if stripe_invoice.get('payment_intent'):
                intent = stripe_invoice.payment_intent
            else :
                intent = stripe_subscription.pending_setup_intent
                
            if intent:
                if not intent.payment_method.customer:
                    stripe.PaymentMethod.attach(
                        intent.payment_method.id,
                        customer=data_object.customer,
                    )
                if not stripe_subscription.default_payment_method:
                    stripe.Subscription.modify (
                        data_object.parent.subscription_details.subscription,
                        default_payment_method=intent.payment_method.id,
                        payment_settings={
                            'payment_method_types': ['card']                    
                        }
                    )

                    customer = stripe.Customer.retrieve(data_object.customer)

                if not customer.invoice_settings.default_payment_method:
                    stripe.Customer.modify(
                        data_object.customer,
                        invoice_settings={
                            'default_payment_method': intent.payment_method.id
                        }
                    )
            
            try:
                subscription = models.Subscription.objects.select_related(
                    'user',
                    'customer'   
                ).get(stripe_id = data_object.parent.subscription_details.subscription)
                item = stripe.SubscriptionItem.list(
                    limit=1,
                    subscription=subscription.stripe_id
                )
                if subscription.plan.stripe_id != item.data[0].price.id:
                    try:
                        plan = models.Plan.objects.get(stripe_id=item.data[0].price.id)
                        subscription.plan = plan
                        subscription.save()
                    except models.Plan.DoesNotExist:
                        return JsonResponse({'no such plan price': item.data[0].price.id}, status=422)              
                if subscription.plan.life and data_object.amount_paid == data_object.amount_due and data_object.amount_due > 0:
                    stripe.Subscription.modify(
                        subscription.stripe_id,
                        cancel_at_period_end=True
                    )
            except models.Subscription.DoesNotExist:
                return JsonResponse({'no such subscription': data_object.parent.subscription_details.subscription}, status=422)
        except models.Invoice.DoesNotExist:
            return JsonResponse({'no such invoice': data_object.id}, status=422)
        
    elif event_type == 'invoice.finalized':
        response = requests.get(data_object.invoice_pdf)
        try:            
            invoice = models.Invoice.objects.select_related(
                'user',
                'customer',
                'subscription'    
            ).get(stripe_id=data_object.id)
            invoice.status = data_object.status
            invoice.file.save(data_object.id + ".pdf", ContentFile(response.content))
            invoice.save()            
        except models.Invoice.DoesNotExist:
            return JsonResponse({'no such invoice': data_object.id}, status=422)
        
    elif event_type == 'customer.subscription.updated':
        stripe_subscription = stripe.Subscription.retrieve(data_object.id)
        try:
            subscription = models.Subscription.objects.select_related(
                'user',
                'customer'    
            ).get(stripe_id=data_object.id)          
            if subscription.plan.life and data_object.cancel_at:
                subscription.access = True
                subscription.status = "infinite"
            else:
                subscription.status = data_object.status
                subscription.access = True if data_object.status in ['active', 'trialing'] else False                  
                subscription.end = datetime.fromtimestamp(data_object['items']['data'][0].current_period_end)
            subscription.save()
        except models.Subscription.DoesNotExist:
            return JsonResponse({'no such subscription': data_object.id}, status=422)
        
    elif event_type == 'customer.subscription.deleted':
        try:
            subscription = models.Subscription.objects.select_related(
                'user',
                'customer'
            ).get(stripe_id=data_object.id)
            subscription.access = False
            subscription.status = "deleted"
            subscription.save()
        except models.Subscription.DoesNotExist:
            return JsonResponse({'no such subscription': data_object.id}, status=422)
    elif event_type == 'customer.subscription.trial_will_end':
        # to warn the client about the end of the trial period
        pass
    elif event_type == 'customer.deleted':
        try:
            customer = models.Customer.objects.select_related('user').get(stripe_id=data_object.id)
            subscriptions = models.Subscription.objects.filter(user=customer.user)
            customer.delete()
            for subscription in subscriptions:
                subscription.delete()             
        except models.Customer.DoesNotExist:
            return JsonResponse({'no such customer': data_object.id}, status=422)
    elif event_type == 'product.updated':
        try:
            plan = models.Plan.objects.get(product=data_object.id)
            if plan.label.key == "subscription-life":
                plan.life = True
            if not data_object.active:
                plan.active = False
                plan.save()
            else:
                plan.active = True              
        except models.Plan.DoesNotExist:
            new_plan = models.Plan()
            label = TranslationKey.objects.get(key=data_object.name)
            new_plan.label = label
            if label.key == "subscription-life":
                new_plan.life = True
            new_plan.product = data_object.id
            price = stripe.Price.retrieve(data_object.default_price)
            new_plan.price = price.unit_amount/100
            new_plan.stripe_id = data_object.default_price
            new_plan.active = True
            new_plan.save()
    return JsonResponse({'result': 'success'})

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
    invoices = models.Invoice.objects.select_related(
        'user',
        'customer',
        'subscription'    
    ).filter(user=userId).order_by('-mdate')
    return invoices

@router.get('/invoice/download/{id}', response=List[schemas.InvoiceSchema])
def download(request, id: int):
    userId = request.user.id
    try:
        invoice = models.Invoice.objects.select_related(
            'user',
            'customer',
            'subscription'    
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
        userId = request.user.id
        customer = models.Customer.objects.select_related('user').get(user=userId)
        price = stripe.Price.retrieve(plan.stripe_id)
    except models.Plan.DoesNotExist:
        return JsonResponse({'error': "no-plan-available"})
    except models.Customer.DoesNotExist:
        return JsonResponse({'error': "no-customer"})
    
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
