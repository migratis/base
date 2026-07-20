from django.contrib import admin
from . import models


@admin.register(models.Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("cdate", "mdate", "user", "stripe_id",)
    search_fields = ('cdate', 'mdate', 'user__email', 'stripe_id',)


@admin.register(models.StripePayment)
class StripePaymentAdmin(admin.ModelAdmin):
    list_display = ("cdate", "user", "purpose", "amount", "currency", "status", "stripe_session_id",)
    search_fields = ('user__email', 'purpose', 'stripe_session_id',)


@admin.register(models.Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("cdate", "mdate", "customer", "purpose", "status", "label_key", "reference", "stripe_id",)
    search_fields = ('user__email', 'customer__stripe_id', 'purpose', 'reference', 'label_key', 'stripe_id',)
