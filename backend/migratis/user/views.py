from http.client import OK
import six
import secrets
from datetime import timedelta
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import EmailMessage
from django.conf import settings
from smtplib import SMTPRecipientsRefused
from ninja import Form, Router
from migratis.api.functions import formatErrors
from migratis.i18n.views import t
from migratis.api.decorators import check_access
from migratis.api import billing
from . import models, schemas
from pprint import pprint


router = Router()

TFA_COOKIE_NAME = 'tfa_verified'
TFA_COOKIE_DURATION = 7  # days the trusted-device cookie keeps the user from re-verifying


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
            to=[user.email],
        )
        email.send()
        return True
    except SMTPRecipientsRefused:
        return False


def sendActivation(user):
    try:
        mail_subject = '[' + settings.SITE_NAME + '] ' + \
        t('confirm-registration', user.language, 'email')
        message = render_to_string(user.language + '.active_email.html', {
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
        return True
    except SMTPRecipientsRefused as e:
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
        user.trial = billing.has_trial(user)
        user.subscription = billing.active_subscription(user)
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
        user.trial = billing.has_trial(user)
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
           return JsonResponse({"detail": formatErrors(error)}, status=422) 
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
        if billing.save_customer(token_user):
            token_user.is_active = True
            token_user.save()
        else:
           return JsonResponse({"detail": formatErrors({"taxnumber": ["taxnumber-invalid"]})}, status=422) 
        return JsonResponse({"detail": [{"success": ["invitation-successfull"]}]})
    except ValidationError as e:
        if (user.id is not None): user.delete()
        return JsonResponse({"detail": formatErrors(e.message_dict)}, status=422)

@router.post('/register', auth=None)
def _assign_default_registration_groups(user):
    """Add a freshly-confirmed account to the installed module's default role
    group(s). Base stays role-agnostic: the group names come from the
    DEFAULT_REGISTRATION_GROUPS setting, which the installed app's
    settings_patch declares (mirrors roles.DEFAULT_AUTH_ROLE). Superusers
    outrank any ladder, so they are skipped. Idempotent."""
    if getattr(user, 'is_superuser', False):
        return
    from django.contrib.auth.models import Group
    for gname in getattr(settings, 'DEFAULT_REGISTRATION_GROUPS', []):
        group, _ = Group.objects.get_or_create(name=gname)
        user.groups.add(group)


def register(request, user: Form[schemas.UserSchemaIn]):
    user = models.User(**user.dict())
    try:
        user.is_active = False
        user.save()
        if not billing.save_customer(user):
            user.delete()
            return JsonResponse({"detail": formatErrors({"taxnumber": ["taxnumber-invalid"]})}, status=422) 
        if not sendActivation(user):
            return JsonResponse({"detail": formatErrors({"email": ["email-refused"]})}, status=422)
        return JsonResponse({"detail": [{"success": ["confirm-link-in-email"]}]})
    except ValidationError as e:
        if (user.id is not None): user.delete()
        return JsonResponse({"detail": formatErrors(e.message_dict)}, status=422)
    
@router.post('/activate', auth=None)
@csrf_exempt
def activate(request, uidb64: Form[str], token: Form[str]):
    try:
        uid = int(urlsafe_base64_decode(uidb64).decode())
        user = models.User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, models.User.DoesNotExist):
        user = None
    if user is not None:
        if user.is_active == True:
            return JsonResponse({"detail": formatErrors({"active": ["registration-confirmation-done"]})}, status=422)
        if account_pass_token.check_token(user, token):
            user.is_active = True
            if user.old_passwords is not None:
                if len(user.old_passwords) >= 6:
                    user.old_passwords.remove()
                user.old_passwords.append(make_password(user.password))
            else:
                user.old_passwords = [make_password(user.password)]
            user.save()
            _assign_default_registration_groups(user)
            return JsonResponse({"detail": [{"success": ["registration-confirmed"]}]})
        else:
            return JsonResponse({"detail": formatErrors({"token": ["registration-confirmation-failed"]})}, status=422)
    return JsonResponse({"detail": formatErrors({"user": ["user-not-exists"]})}, status=422)

def _user_session_payload(user):
    """Build the authenticated /login response body (trial + subscription state).
    `groups` + `is_superuser` let installed-module frontends resolve the
    viewer's role ladder tier (their roles.py maps auth Groups to roles)
    without an extra round-trip."""
    user.trial = billing.has_trial(user)
    sub = billing.active_subscription(user)
    user.subscription = sub.status if sub else None
    return {
        "user": {
            "id": user.id,
            "trial": user.trial,
            "subscription": user.subscription,
            'country': user.country_code,
            "groups": list(user.groups.values_list('name', flat=True)),
            "is_superuser": bool(user.is_superuser),
        }
    }


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
        if not user.is_active:
            sendActivation(user)
            return JsonResponse({"detail": formatErrors({"email": ['account-not-activated']})}, status=400)
        if user.deleted:
            return JsonResponse({"detail": formatErrors({"email": ['account-deleted']})}, status=400)
    except models.User.DoesNotExist:
        pass

    result = authenticate(username=email, password=password)

    if result is not None:
        user = models.User.objects.get(pk=result.id)
        # Trusted device: a valid tfa_verified cookie skips the code step for a week.
        if request.COOKIES.get(TFA_COOKIE_NAME):
            django_login(request, result)
            return JsonResponse(_user_session_payload(user))
        # Otherwise email a one-time code and ask the frontend to collect it.
        sendTFA(user)
        return JsonResponse({
            "tfa_required": True,
            "email": email,
            "remember_device": remember,
        })
    return JsonResponse({"detail": formatErrors({"email": ["user-unknown-or-wrong-credentials"]})}, status=400)


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

    django_login(request, user)
    user.tfa_code = None
    user.tfa_code_expires = None
    user.tfa_attempts = 0
    user.save()

    response = JsonResponse(_user_session_payload(user))
    if remember:
        response.set_cookie(
            TFA_COOKIE_NAME,
            'verified',
            max_age=60 * 60 * 24 * TFA_COOKIE_DURATION,
            samesite='Lax',
            httponly=True,
        )
    return response


@router.post('/tfa/resend', auth=None)
@csrf_exempt
def tfaResend(request, email: Form[str]):
    if email == "":
        return JsonResponse({"detail": formatErrors({"email": ['email-missing']})}, status=400)
    try:
        user = models.User.objects.get(email=email)
    except models.User.DoesNotExist:
        # Do not reveal whether the account exists.
        return JsonResponse({"detail": [{"success": ["tfa-code-sent"]}]})
    sendTFA(user)
    return JsonResponse({"detail": [{"success": ["tfa-code-sent"]}]})


@router.get('/logout')
def logout(request):
    if not request.user.is_authenticated:
        return JsonResponse({'detail': [{ 'error': "user-not-connected"}]}, status=400)

    django_logout(request)
    return JsonResponse({'detail': [{ 'success': 'logout-successfully'}]})

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