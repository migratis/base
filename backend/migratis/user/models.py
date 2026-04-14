from django.db.models import JSONField
from django.contrib.auth.hashers import make_password, check_password
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django_countries.fields import CountryField
from migratis.i18n.models import LANGUAGES
from pprint import pprint

class SaveMixin:

    def save(self, *args, **kwargs):
        if hasattr(self, 'confPassword'):
            try:
                self.password = make_password(self.password)
                self.full_clean()
                if self.old_passwords is not None:
                    if len(self.old_passwords) >= 6:
                        self.old_passwords.pop(0)
                    self.old_passwords.append(self.password)
                else:
                    self.old_passwords = [self.password]
            except ValidationError as e:
                message = {}
                for key in e.message_dict:
                    if e.message_dict[key][0] == 'This field cannot be blank.':
                        message[key] = 'empty-field'
                    elif e.message_dict[key][0] == 'Customer with this Email already exists.':
                        message[key] = 'email-exists'
                    else:
                        message[key] = e.message_dict[key][0]
                raise ValidationError(message)
            
        return super(SaveMixin, self).save(*args, **kwargs)

class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Users require an email field')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)
    
class User(SaveMixin, AbstractUser):

    def __init__(self, *args, **kwargs):
        confPassword = kwargs.pop('confPassword', None)
        if confPassword is not None:
            self.confPassword = confPassword
        kwargs.pop('uidb64', None)
        kwargs.pop('token', None)                     
        super(User, self).__init__(*args, **kwargs)

    username = None
    email = models.EmailField(max_length=150, unique=True)
    first_name = models.CharField(max_length=30, null=False)
    last_name = models.CharField(max_length=150, null=False)
    birthdate = models.DateField(null=True, blank=True)
    language = models.CharField(max_length=2, choices=LANGUAGES, null=False)
    professional = models.BooleanField(default=False)
    company = models.CharField(max_length=30, null=True, blank=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    city = models.CharField(max_length=150, null=True, blank=True)
    zipcode = models.CharField(max_length=20, null=True, blank=True, validators=[RegexValidator(r'^\w{1}\-\d{1,4}$|^\d{1,10}$')])   
    taxnumber = models.CharField(max_length=30, null=True, blank=True)
    country = CountryField(max_length=2, null=True, blank=False)
    cgu = models.BooleanField(default=False)  
    old_passwords = JSONField(null=True, blank=True)  # list of hashed passwords; JSONField works with SQLite and PostgreSQL
    deleted = models.BooleanField(default=False)  
    cdate = models.DateTimeField(auto_now_add=True)
    mdate = models.DateTimeField(auto_now=True) 
    
    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'country', 'language']

    def __str__(self):
        return self.email

    def clean(self, *args, **kwargs):
        errors = {}
        if hasattr(self, 'confPassword'):
            if self.confPassword is None:
                errors["confPassword"] = "empty-field"
            if not self.check_password(self.confPassword):
                errors["password"] = "passwords-not-match"
                errors["confPassword"] = "passwords-not-match"
            if self.old_passwords is not None:
                for old_password in self.old_passwords:
                    if check_password(self.password, old_password):
                        errors["password"] = "password-already-used"
            if self.cgu is False:
                errors["cgu"] = "must-accept-cgu"
        if self.professional is True:
            if self.company is None:
                errors["company"] = "field required"
            if self.taxnumber is None:
                errors["taxnumber"] = "field required"                
            if self.address is None:
                errors["address"] = "field required"
            if self.city is None:
                errors["city"] = "field required"                
            if self.zipcode is None:
                errors["zipcode"] = "field required"
                
        if bool(errors):
            raise ValidationError(errors)
    
    @property
    def country_code(self):
        return self.country.code

        