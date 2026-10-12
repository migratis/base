from ninja import ModelSchema
from . import models


class CookieSchema(ModelSchema):
    # Derived on the model from `category`, so the page and the notice cannot
    # read a consent requirement that disagrees with the stated purpose.
    requires_consent: bool

    class Meta:
        model = models.Cookie
        fields = [
            'id', 'name', 'provider', 'description',
            'storage', 'category', 'retention_unit', 'retention_value',
        ]
