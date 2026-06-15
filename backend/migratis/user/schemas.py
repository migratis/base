from ninja import ModelSchema
from pydantic import EmailStr, Field
from django.conf import settings
from . import models

# Only bind the subscription app's schema when subscriptions are enforced; when
# disabled the field is a passthrough (always None), so the user module does not
# import — or depend on — the optional subscription app.
if settings.NO_SUBSCRIPTION:
    from typing import Any as SubscriptionField
else:
    from typing import Optional
    from migratis.subscription.schemas import SubscriptionSchema
    SubscriptionField = Optional[SubscriptionSchema]

class UserSchemaInMin(ModelSchema):
    email : EmailStr | None = Field(default=None)

    class Meta:
        model = models.User
        fields = ['email', 'first_name', 'last_name', 'language', 'country']


class UserSchemaIn(ModelSchema):
    confPassword: str
    professional: bool | None = False
    company: str | None = None
    taxnumber: str | None = None
    address: str | None = None
    city: str | None = None
    zipcode: str | None = None
    email : EmailStr | None = Field(default=None)

    class Meta:
        model = models.User
        fields = ['email', 'password', 'first_name', 'last_name', 'language', 'birthdate', 'country', 'professional', 'company', 'taxnumber', 'address', 'zipcode', 'city', 'cgu']

class UserSchemaInvitation(ModelSchema):
    uidb64: str
    token: str
    confPassword: str
    professional: bool | None = False
    company: str | None = None
    taxnumber: str | None = None
    address: str | None = None
    city: str | None = None
    zipcode: str | None = None
    email : EmailStr | None = Field(default=None)

    class Meta:
        model = models.User
        fields = ['email', 'password', 'first_name', 'last_name', 'language', 'birthdate', 'country', 'professional', 'company', 'taxnumber', 'address', 'zipcode', 'city', 'cgu']


class UserSchemaUpdateIn(ModelSchema):
    professional: bool | None = False
    company: str | None = None
    taxnumber: str | None = None
    address: str | None = None
    city: str | None = None
    zipcode: str | None = None
    
    class Meta:
        model = models.User
        fields = ['language', 'first_name', 'last_name', 'birthdate', 'address', 'zipcode', 'city', 'country', 'professional', 'company', 'taxnumber', 'address', 'zipcode', 'city', ]

class UserSchemaOut(ModelSchema):
    country_code: str | None = None
    professional: bool | None = False
    company: str | None = None
    taxnumber: str | None = None
    address: str | None = None
    city: str | None = None
    zipcode: str | None = None
    subscription: SubscriptionField = None
    trial: bool = True
    # `groups` (by name) + `is_superuser` let installed-module frontends resolve
    # the viewer's role-ladder tier. Must mirror the /login payload shape
    # (`_user_session_payload`) so the Layout profile-refresh that overwrites
    # localStorage.user does not strip role identity.
    groups: list[str] = []

    @staticmethod
    def resolve_groups(obj):
        return list(obj.groups.values_list('name', flat=True))

    class Meta:
        model = models.User
        fields = ['id', 'email', 'first_name', 'last_name', 'language', 'birthdate', 'address', 'zipcode', 'city', 'company', 'taxnumber', 'is_superuser']
