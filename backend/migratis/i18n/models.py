from django.db import models

LANGUAGES = [
    ("fr", "Français"),
    ("en", "English"),
    ("es", "Español"),
    ("ro", "Română"),    
]

class TranslationNameSpace(models.Model):
    ns = models.CharField(max_length=50, null=False)
   
    class Meta:
        verbose_name_plural = "Namespaces"
        
    def __str__(self):
        return self.ns

class TranslationKey(models.Model):
    ns = models.ManyToManyField(TranslationNameSpace, related_name='key_name_spaces')
    key = models.CharField(max_length=500, null=False)
   
    class Meta:
        verbose_name_plural = "Translations"
        
    def __str__(self):
        return self.key

class TranslationText(models.Model):
    key = models.ForeignKey(TranslationKey, on_delete=models.CASCADE, related_name='keys')
    lng = models.CharField(max_length=2, choices=LANGUAGES, null=False)
    text = models.TextField(null=False)
   
    class Meta:
        unique_together = (('key', 'lng'),)
    def __str__(self):
        return self.key.key + " - " + self.lng 
