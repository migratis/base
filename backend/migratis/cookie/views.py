from django.http import JsonResponse
from typing import List
from ninja import Router
from migratis.api.functions import formatErrors
from . import models, schemas
from pprint import pprint

router = Router()

@router.get('/list/', response=List[schemas.CookieSchema], auth=None)
def getBanksList(request):
    try:
        cookies = models.Cookie.objects.all()
    except(TypeError, ValueError, OverflowError, models.Cookie.DoesNotExist):
        cookies = None

    if cookies is not None:
        return cookies

    return JsonResponse({"detail": formatErrors({"cookie": ["cookie-not-exists"]})}, status=422)   
