from ninja import ModelSchema
from . import models

class TranslationKeySchema(ModelSchema):
    key: str | None = None
    class Meta:
        model = models.TranslationKey
        fields = ['key']
