from ninja import Router
from . import models

router = Router()

def t(key: str, lng: str, ns: str):
    try:
        translation = models.TranslationText.objects.get(lng=lng, key__key=key, key__ns__ns=ns)
        return translation.text
    except models.TranslationText.DoesNotExist:
        return key

@router.get('/', auth=None)
def i18n(request, ns: str, lng: str):
    content = {} 
    try:
        ns_object = models.TranslationNameSpace.objects.get(ns=ns)
        translations = models.TranslationText.objects.select_related('key').filter(lng=lng, key__ns__in=[ns_object])
        for translation in translations:
            content[translation.key.key] = translation.text
        return content
    except models.TranslationNameSpace.DoesNotExist:
        return content
