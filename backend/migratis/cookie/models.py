from django.db import models
from migratis.i18n.models import TranslationKey

class Cookie(models.Model):
    name = models.CharField(max_length=500, null=False)
    provider = models.CharField(max_length=50, null=False)    
    description = models.ForeignKey(TranslationKey, related_name='translation_cookie_descriptions', on_delete=models.PROTECT)
    cdate = models.DateTimeField(auto_now_add=True)
    mdate = models.DateTimeField(auto_now=True) 
    
    class Meta:
         verbose_name_plural = "cookies"

    def __str__(self):
        return self.name
