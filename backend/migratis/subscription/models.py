from django.db import models
from migratis.user.models import User
from migratis.i18n.models import TranslationKey

TAX_ID_TYPE = {
    "ZA": "za_vat",
    "DE": "eu_vat",
    "SA": "sa_vat",
    "AU": "au_abn",
    #"AU": "au_arn",
    "AT": "eu_vat",
    "BE": "eu_vat",
    "BR": "br_cnpj",
    #"BR": "br_cpf",
    "BG": "bg_uic",
    "BG": "eu_vat",
    "CA": "ca_bn",
    #"CA": "ca_gst_hst",
    #"CA": "ca_pst_bc",
    #"CA": "ca_pst_mb",
    #"CA": "ca_pst_sk",
    #"CA": "ca_qst",
    "CL": "cl_tin",
    "CY": "eu_vat",
    "CR": "kr_brn",
    "HR": "eu_vat",
    "DK": "eu_vat",
    "EG": "eg_tin",
    "AE": "ae_trn",
    #"ES": "es_cif",
    "ES": "eu_vat",
    "EE": "eu_vat",
    "US": "us_ein",
    "EU": "eu_oss_vat",
    "FI": "eu_vat",
    "FR": "eu_vat",
    "GE": "ge_vat",
    "GR": "eu_vat",
    "HK": "hk_br",
    "HU": "eu_vat",
    #"HU": "hu_tin",
    "IN": "in_gst",
    "ID": "id_npwp",
    "IE": "eu_vat",
    "IS": "is_vat",
    "IL": "il_vat",
    "IT": "eu_vat",
    "JP": "jp_cn",
    #"JP": "jp_rn",
    #"JP": "jp_trn",
    "KE": "ke_pin",
    "LV": "eu_vat",
    "LI": "li_uid",
    "LT": "eu_vat",
    "LU": "eu_vat",
    "MY": "my_frp",
    #"MY": "my_itn",
    #"MY": "my_sst",
    "MT": "eu_vat",
    "MX": "mx_rfc",
    "NO": "no_vat",
    "NZ": "nz_gst",
    "NL": "eu_vat",
    "PH": "ph_tin",
    "PL": "eu_vat",
    "PT": "eu_vat",
    "CZ": "eu_vat",
    "RO": "eu_vat",
    #"GB": "eu_vat",
    "GB": "gb_vat",
    "RU": "ru_inn",
    #"RU": "ru_kpp",
    "SG": "sg_gst",
    "SG": "sg_uen",
    "SK": "eu_vat",
    "SI": "eu_vat",
    #"SI": "si_tin",
    "SE": "eu_vat",
    "CH": "ch_vat",
    "TW": "tw_vat",
    "TH": "th_vat",
    "TR": "tr_tin",
    "UA": "ua_vat"
}

class Plan(models.Model):
    label = models.ForeignKey(TranslationKey, on_delete=models.PROTECT)
    product = models.CharField(max_length=50, null=False)
    price = models.DecimalField(default=0, max_digits=99, decimal_places=2)
    stripe_id = models.CharField(max_length=50, null=False)
    active = models.BooleanField(default=False)
    life = models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = "Plans"

    def __str__(self):
        return self.label.key + " (" + ("active" if self.active else "inactive") + ")"

class Customer(models.Model):
    user  = models.ForeignKey(User, on_delete=models.CASCADE, unique=False,)
    cdate = models.DateTimeField(auto_now_add=True)
    mdate = models.DateTimeField(auto_now=True) 
    stripe_id = models.CharField(max_length=50, null=False)

    class Meta:
        verbose_name_plural = "Customers"

    def __str__(self):
        return self.user.email + " " + self.stripe_id + " " + str(self.cdate) + " " + str(self.mdate)  

class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, unique=False,)
    customer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING, unique=False, null=True,)
    plan = models.ForeignKey(Plan, on_delete=models.DO_NOTHING, unique=False,)
    cdate = models.DateTimeField(auto_now_add=True)
    mdate = models.DateTimeField(auto_now=True) 
    access = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default="incomplete")
    end = models.DateTimeField(null=True)
    stripe_id = models.CharField(max_length=50, null=False)
    cancelled = models.BooleanField(default=False)  
    
    class Meta:
        verbose_name_plural = "Subscriptions"

    def __str__(self):
        return str(self.mdate) + " " + self.user.email + " " + self.stripe_id + " " + str(self.access)  
  
class Invoice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, unique=False,)
    customer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING, unique=False, null=True,)    
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, unique=False,)
    plan = models.ForeignKey(Plan, on_delete=models.DO_NOTHING, unique=False,)
    cdate = models.DateTimeField(auto_now_add=True)
    mdate = models.DateTimeField(auto_now=True) 
    status = models.CharField(max_length=20, default="draft")
    file = models.FileField(upload_to='migratis/subscription/invoices', blank=True, null=True,)
    stripe_id = models.CharField(max_length=50, null=False)
    amount = models.DecimalField(default=0, max_digits=99, decimal_places=2)
    tax = models.DecimalField(default=0, max_digits=99, decimal_places=2)
    
    class Meta:
        verbose_name_plural = "Invoices"

    def __str__(self):
        return str(self.mdate) + " " + self.user.email + " " + self.status + " " + self.stripe_id