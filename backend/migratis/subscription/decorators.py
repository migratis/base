from functools import wraps
from django.http import JsonResponse
from django.conf import settings
from migratis.api.functions import formatErrors
from ninja.errors import HttpError

from . import models

def test_access(user):
    if settings.NO_SUBSCRIPTION:
        return True 
        
    access = models.Subscription.objects.select_related("user").filter(user=user.id, access=True)
    if access:
        return True
    return False

def check_access():
    def decorator(view):
        @wraps(view)
        def _wrapped_view(request, *args, **kwargs):
            if not test_access(request.user):
                raise HttpError(403, "Forbidden") 
            return view(request, *args, **kwargs)
        return _wrapped_view
    return decorator