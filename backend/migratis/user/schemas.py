from ninja import ModelSchema
from pydantic import EmailStr, Field
from . import models
from migratis.subscription.schemas import SubscriptionSchema

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
    country_code: str
    professional: bool | None = False
    company: str | None = None
    taxnumber: str | None = None
    address: str | None = None
    city: str | None = None
    zipcode: str | None = None
    subscription: SubscriptionSchema | None = None
    trial: bool = True
    
    class Meta:
        model = models.User
        fields = ['id', 'email', 'first_name', 'last_name', 'language', 'birthdate', 'address', 'zipcode', 'city', 'company', 'taxnumber']
