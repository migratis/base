from ninja import ModelSchema
from . import models

class CookieSchema(ModelSchema):
    class Meta:
        model = models.Cookie
        fields = ['id', 'name', 'provider', 'description']