from http.client import OK
import six
import secrets
from datetime import timedelta
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.utils import timezone
from django.core.mail import EmailMessage
from django.conf import settings
from smtplib import SMTPException, SMTPRecipientsRefused
import logging
from ninja import Form, Router
from migratis.api.functions import formatErrors
from migratis.i18n.views import t
# NOT `migratis.subscription.*`. In THIS repo the subscription and
# stripe_payment apps are optional and ship commented out of INSTALLED_APPS, so
# a module-level import of them crashes the whole backend at boot the moment the
# installer un-comments the user router in api/views.py: the chain reaches
# `stripe_payment.models.Customer`, a model in an app that is not installed, and
# Django raises. That blocked every generated app using the framework `user`
# module.
#
# migratis' own copy of this file DOES import subscription directly, because
# there it is always installed. **That divergence is deliberate and must
# survive the next port** — this coupling arrived by porting migratis' file
# wholesale over base's decoupled one (f061a61), which is why `api/billing.py`
# and `api/decorators.py` existed, unused, while the backend would not start.
from migratis.api.decorators import check_access
from migratis.api import billing
from . import models, schemas
from pprint import pprint

logger = logging.getLogger(__name__)


TFA_COOKIE_NAME = 'tfa_verified'
TFA_COOKIE_DURATION = 7  # days


router = Router()

# NOTE: the Personal Access Token endpoints are NOT here on purpose.
#
# `PersonalAccessToken` is Migratis' *agent-lane* credential — a bearer token an
# agent uses to drive the generator API on migratis.ai. A generated application
# has no agent lane, so the model, its schema and its migration do not exist in
# this repo, and the router that was ported here with the rest of this file
# referenced all three: `AttributeError: module 'migratis.user.schemas' has no
# attribute 'TokenSchemaOut'` at import time, which is the whole backend failing
# to boot the moment the installer un-commented the user router.
#
# Same cause as the subscription imports above: migratis' copy of this file was
# ported wholesale over base's. **If you port that file again, drop this block
# again** — or port `PersonalAccessToken`, its schema and a migration with it,
# and be able to say what an installed app would do with a credential for an API
# it does not have.


def sendTFA(user):
    try:
        code = str(secrets.randbelow(1000000)).zfill(6)
        user.tfa_code = code
        user.tfa_code_expires = timezone.now() + timedelta(minutes=5)
        user.tfa_attempts = 0
        user.save()

        mail_subject = '[' + settings.SITE_NAME + '] ' + t('tfa-email-subject', user.language, 'email')
        message = render_to_string(user.language + '.tfa_email.html', {
            'app': settings.SITE_NAME,
            'user': user,
            'code': code,
        })
        email = EmailMessage(
            mail_subject,
            message,
            from_email=settings.EMAIL_SENDER,
            to=[user.email]
        )
        email.send()
        return True
    except SMTPRecipientsRefused:
        return False
    except (SMTPException, OSError):
        # A refused recipient was never the only way this fails: an unreachable
        # or slow mail host raises OSError (socket.timeout is a subclass). This
        # runs inline inside POST /login, so letting it escape turns a login
        # into a 500 — and before EMAIL_TIMEOUT was set, into a 60s nginx 504.
        # Report a failed send so the caller can say so rather than promise a
        # code that will never arrive.
        logger.exception('TFA email send failed for user %s', user.pk)
        return False


def sendInvitation(template, subject, userFrom, userTo, item):
    try:
        mail_subject = subject
        message = render_to_string(template, {
            'url': settings.FRONTEND_URL,
            'app': settings.SITE_NAME,
            'userTo': userTo,
            'userFrom': userFrom,
            'item': item,
            'uidb64': urlsafe_base64_encode(force_bytes(userTo.pk)),
            'token': account_pass_token.make_token(userTo),
        })
        email = EmailMessage(
            mail_subject,
            message,
            from_email=settings.EMAIL_SENDER,
            reply_to=[userFrom.email,],                
            to=[userTo.email]
        )
        email.send()
        return True
    except SMTPRecipientsRefused as e:
        return False

@router.get('/userexists/{email}')
@check_access()
def userexists(request, email: str):
    user = models.User.objects.get(pk=request.user.id)
    if email == user.email:
        return JsonResponse({"detail": formatErrors({"user": ["give-another-email"]})}, status=422)
    try:
        internaut = models.User.objects.get(email=email)
    except models.User.DoesNotExist:
        return JsonResponse({"detail": formatErrors({"user": ["collaborator-not-found"]})}, status=422)    
    except(TypeError, ValueError, OverflowError):
        return JsonResponse({"detail": formatErrors({"user": ["unknown-error"]})}, status=422)
    return JsonResponse({"detail": [{"success": ["user-exist"]}]})

@router.post('/create', response=schemas.UserSchemaOut)
@check_access()
def create(request, user: Form[schemas.UserSchemaInMin]):
    user = models.User(**user.dict())
    try:
        user.is_active = False
        user.save()
        return JsonResponse({"success": ["collaborator-invited"]})
    except ValidationError as e:
        if (user.id is not None): user.delete()
        return JsonResponse({"detail": formatErrors(e.message_dict)}, status=422)

@router.get('/getprofile', response=schemas.UserSchemaOut)
def getProfile(request):
    try:
        userId = request.user.id
        user = models.User.objects.get(pk=userId)
        trial = billing.has_trial(user)
        user.trial = trial
        user.subscription = billing.active_subscription(userId)
    except(TypeError, ValueError, OverflowError, models.User.DoesNotExist):
        user = None
    if user is not None:
        return user
    return JsonResponse({"detail": formatErrors({"user": ["user-not-exists"]})}, status=422)   

@router.get('/getprofile/{uidb64}/{token}', auth=None, response=schemas.UserSchemaOut)
def getProfileWithToken(request, uidb64: str, token: str):
    try:
        uid = int(urlsafe_base64_decode(uidb64).decode())
        user = models.User.objects.get(pk=uid)    
        if user is not None and not account_pass_token.check_token(user, token):
            return JsonResponse({"detail": formatErrors({"error": ["invitation-outdated-token"]})}, status=422)     
        trial = billing.has_trial(user)
        user.trial = trial
        user.subscription = billing.active_subscription(user)
    except(TypeError, ValueError, OverflowError, models.User.DoesNotExist):
        user = None
    if user is not None:
        return user
    return JsonResponse({"detail": formatErrors({"user": ["user-not-exists"]})}, status=422)  

@router.post('/update', response=schemas.UserSchemaOut)
def update(request, profile: Form[schemas.UserSchemaUpdateIn]):
    userId = request.user.id
    try:
        user = models.User.objects.get(pk=userId)
        for attr, value in profile.dict().items():
            setattr(user, attr, value)
        savedCustomer, error = billing.save_customer(user)
        if savedCustomer:
            user.save()
        else:
           return JsonResponse({"detail": formatErrors(billing.stripe_error_dict(error))}, status=422)
        return JsonResponse({"detail": [{"success": ["update-successful"]}]})
    except ValidationError as e:
        return JsonResponse({"detail": formatErrors(e.message_dict)}, status=422)
    
@router.post('/delete', response=schemas.UserSchemaOut)
def delete(request):
    userId = request.user.id            
    try:        
        user = models.User.objects.get(pk=userId)                    
        if billing.has_access(user):
            response = billing.do_unsubscribe(user.id)            
    except Exception as e:
        pass
    try:
        user.deleted = True
        user.save()
        return JsonResponse(response)
    except Exception :
        return JsonResponse({"detail": [{"error": ["delete-profile-error"]}]})

@router.post('/invitation', auth=None)
def invitation(request, user: Form[schemas.UserSchemaInvitation]):    
    try:
        uid = int(urlsafe_base64_decode(user.uidb64).decode())
        token_user = models.User.objects.get(pk=uid)    
        if token_user is not None and not account_pass_token.check_token(token_user, user.token):
            return JsonResponse({"detail": formatErrors({"error": ["invitation-outdated-token"]})}, status=422)        
        delattr(user, 'email')
        for attr, value in user.dict().items():
            setattr(token_user, attr, value)
        savedCustomer, error = billing.save_customer(token_user)
        if savedCustomer:
            token_user.is_active = True
            token_user.save()
        else:
           return JsonResponse({"detail": formatErrors(billing.stripe_error_dict(error))}, status=422)
        return JsonResponse({"detail": [{"success": ["invitation-successfull"]}]})
    except ValidationError as e:
        if (user.id is not None): user.delete()
        return JsonResponse({"detail": formatErrors(e.message_dict)}, status=422)

@router.post('/register', auth=None)
def register(request, user: Form[schemas.UserSchemaIn]):
    user = models.User(**user.dict())
    try:
        user.is_active = True
        user.save()
        # saveCustomer returns a (saved, error) TUPLE — truth-testing the tuple
        # itself can never fail (PoC #20 continuation): unpack it.
        savedCustomer, error = billing.save_customer(user)
        if not savedCustomer:
            user.delete()
            return JsonResponse({"detail": formatErrors(billing.stripe_error_dict(error))}, status=422)
        return JsonResponse({"detail": [{"success": ["registration-success"]}]})
    except ValidationError as e:
        if (user.id is not None): user.delete()
        return JsonResponse({"detail": formatErrors(e.message_dict)}, status=422)
    
# No /activate endpoint: registration activates the account directly. Proving
# the address is reachable is the 2FA code's job — login mails a code to it and
# grants no session until it comes back, so a separate confirmation link added a
# second round-trip that gated nothing. Invited collaborators are activated by
# /invitation, which has always had its own path and never used this one.


@router.post('/login', auth=None)
@csrf_exempt
def login(request, email: Form[str], password: Form[str], remember_device: Form[str] = 'true'):
    remember = remember_device.lower() == 'true'
    
    if email == "" or password == "":
        error = {}
        if email == "":
            error['email'] = ['email-missing']
        if password == "":
            error['password'] = ['password-missing']
        return JsonResponse({"detail": formatErrors(error)}, status=400)
        
    try:
        user = models.User.objects.get(email=email)
        if user.deleted:
            return JsonResponse({"detail": formatErrors({"email": ['account-deleted']})}, status=400)
    except models.User.DoesNotExist:
        pass
    
    result = authenticate(username=email, password=password)

    if result is not None:
        tfa_cookie = request.COOKIES.get(TFA_COOKIE_NAME)
        
        if tfa_cookie:
            django_login(request, result, backend='django.contrib.auth.backends.ModelBackend')
            user = models.User.objects.get(pk=result.id)
            user.trial = billing.has_trial(user)
            subscription = billing.active_subscription(user)
            user.subscription = subscription.status if subscription else None
            response = JsonResponse({ 
                "user": {
                    "id": user.id,
                    "trial": user.trial,
                    "subscription": user.subscription,
                    'country': user.country_code
                }
            })
            return response
        
        if not sendTFA(user):
            # Claiming tfa_required when the mail never left strands the user on
            # a code entry screen with no code coming. 422 rather than a 5xx on
            # purpose: ADMINS is set, so a 5xx here makes Django's
            # AdminEmailHandler call mail_admins() — a second blocking SMTP send
            # inside this same request, at the one moment mail is known broken.
            return JsonResponse(
                {"detail": formatErrors({"email": ["tfa-email-send-failed"]})},
                status=422,
            )
        return JsonResponse({
            "tfa_required": True,
            "email": email,
            "remember_device": remember
        })
    return JsonResponse({"detail": formatErrors({"email": ["user-unknown-or-wrong-credentials"]})}, status=400)

@router.get('/logout')
def logout(request):
    if not request.user.is_authenticated:
        return JsonResponse({'detail': [{ 'error': "user-not-connected"}]}, status=400)

    django_logout(request)
    return JsonResponse({'detail': [{ 'success': 'logout-successfully'}]})


@router.post('/tfa/verify', auth=None)
@csrf_exempt
def tfaVerify(request, email: Form[str], code: Form[str], remember_device: Form[str] = 'true'):
    remember = remember_device.lower() == 'true'
    if email == "" or code == "":
        error = {}
        if email == "":
            error['email'] = ['email-missing']
        if code == "":
            error['code'] = ['tfa-code-required']
        return JsonResponse({"detail": formatErrors(error)}, status=400)
    
    try:
        user = models.User.objects.get(email=email)
    except models.User.DoesNotExist:
        return JsonResponse({"detail": formatErrors({"code": ["tfa-code-invalid"]})}, status=400)
    
    if not user.tfa_code or not user.tfa_code_expires:
        return JsonResponse({"detail": formatErrors({"code": ["tfa-code-invalid"]})}, status=400)
    
    if timezone.now() > user.tfa_code_expires:
        return JsonResponse({"detail": formatErrors({"code": ["tfa-code-expired"]})}, status=400)
    
    if user.tfa_code != code:
        user.tfa_attempts += 1
        user.save()
        if user.tfa_attempts >= 3:
            user.tfa_code = None
            user.tfa_code_expires = None
            user.tfa_attempts = 0
            user.save()
            return JsonResponse({"detail": formatErrors({"code": ["tfa-max-attempts"]})}, status=400)
        return JsonResponse({"detail": formatErrors({"code": ["tfa-code-invalid"]})}, status=400)
    
    django_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    
    user.tfa_code = None
    user.tfa_code_expires = None
    user.tfa_attempts = 0
    user.save()
    
    user = models.User.objects.get(pk=user.id)
    user.trial = billing.has_trial(user)
    subscription = billing.active_subscription(user)
    user.subscription = subscription.status if subscription else None
    
    response = JsonResponse({ 
        "user": {
            "id": user.id,
            "trial": user.trial,
            "subscription": user.subscription,
            'country': user.country_code
        }
    })
    
    if remember:
        response.set_cookie(
            TFA_COOKIE_NAME,
            'verified',
            max_age=60*60*24*TFA_COOKIE_DURATION,
            samesite='Lax',
            httponly=True
        )
    
    return response
    
    return JsonResponse({"detail": formatErrors({"code": ["tfa-code-invalid"]})}, status=400)


@router.post('/tfa/resend', auth=None)
@csrf_exempt
def tfaResend(request, email: Form[str]):
    if email == "":
        return JsonResponse({"detail": formatErrors({"email": ["email-missing"]})}, status=400)
    
    try:
        user = models.User.objects.get(email=email)
    except models.User.DoesNotExist:
        return JsonResponse({"detail": formatErrors({"email": ["user-not-exists"]})}, status=400)
    
    if user.tfa_code and user.tfa_code_expires:
        sent_at = user.tfa_code_expires - timedelta(minutes=5)
        if (timezone.now() - sent_at).total_seconds() < 60:
            return JsonResponse({"detail": formatErrors({"email": ["tfa-resend-rate-limit"]})}, status=400)
    
    sendTFA(user)
    return JsonResponse({"detail": [{"success": ["tfa-code-sent"]}]})


@router.post('/reset_password', auth=None)
@csrf_exempt
def resetPassword(request, email: Form[str]):
    try:
        user = models.User.objects.get(email=email)
    except(TypeError, ValueError, OverflowError, models.User.DoesNotExist):
        user = None
    if user is not None:
        try:
            mail_subject = '[' + settings.SITE_NAME + '] ' + \
                t('change-password', user.language, 'password')
            message = render_to_string(user.language + '.reset_password.html', {
                'url': settings.FRONTEND_URL,
                'app': settings.SITE_NAME,
                'user': user,
                'uidb64': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_pass_token.make_token(user),
            })
            email = EmailMessage(
                mail_subject,
                message,
                from_email=settings.EMAIL_SENDER,
                to=[user.email]
            )
            email.send()
            return JsonResponse({"detail": [{"success": ["reset-link-in-email"]}]})
        except SMTPRecipientsRefused as e:
            return JsonResponse({formatErrors(e.message_dict)}, status=422)
    return JsonResponse({"detail": formatErrors({"email": ["email-not-exists"]})}, status=422)

@router.post('/change_password', auth=None)
@csrf_exempt
def changePassword(request, password: Form[str], confPassword: Form[str], uidb64: Form[str], token: Form[str]):
    try:
        uid = int(urlsafe_base64_decode(uidb64).decode())
        user = models.User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, models.User.DoesNotExist):
        user = None
    if user is not None and account_pass_token.check_token(user, token):
        try:
            user.password = password
            user.confPassword = confPassword
            if not user.last_login:
                user.is_activated = True
            user.save()           
            return JsonResponse({"detail": [{"success": ["password-changed"]}]})
        except ValidationError as e:
            return JsonResponse({"detail": formatErrors(e.message_dict)}, status=422)
    else:
        return JsonResponse({"detail": formatErrors({"error": ["outdated-token"]})}, status=422)
    
@router.post('/connected_change_password')
def changePasswordConnected(request, oldPassword: Form[str], password: Form[str], confPassword: Form[str]):
    try:
        user = models.User.objects.get(pk=request.user.id)
    except(TypeError, ValueError, OverflowError, models.User.DoesNotExist):
        user = None
    if user is not None:
        if not user.check_password(oldPassword):
            return JsonResponse({"detail": formatErrors({"oldPassword": ["old-password-wrong"]})}, status=422)
        try:
            user.password = password
            user.confPassword = confPassword
            if not user.last_login:
                user.is_activated = True
            user.save()
            return JsonResponse({"detail": [{"success": ["password-changed"]}]})
        except ValidationError as e:
            return JsonResponse({"detail": formatErrors(e.message_dict)}, status=422)
    else:
        return JsonResponse({"detail": formatErrors({"error": ["change-password-failed"]})}, status=422)

class TokenGenerator(PasswordResetTokenGenerator):

    def _make_hash_value(request, user, timestamp):
        if  user.is_active:
            active = 'yes'
        else:
            active = 'no'
        return (
            six.text_type(user.pk) + six.text_type(timestamp) +
            six.text_type(active)
        )
        
account_pass_token = TokenGenerator()            