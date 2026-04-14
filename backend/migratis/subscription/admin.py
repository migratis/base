from django.contrib import admin
from . import models
from import_export import resources
from import_export.admin import ImportExportModelAdmin

class PlanResource(resources.ModelResource):

    class Meta:
        model = models.Plan

@admin.register(models.Plan)
class PlanAdmin(ImportExportModelAdmin):
    list_display = ("label", "product", "price", "life", "active", "stripe_id",)
    search_fields = ('label__key', 'product', 'price', 'active', 'stripe_id',)
    
@admin.register(models.Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("cdate", "mdate", "user", "stripe_id",)
    search_fields = ('cdate', 'mdate', 'user__email', 'stripe_id',)

@admin.register(models.Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("cdate", "mdate", "customer", "plan", "access", "status", "end", "stripe_id", "cancelled",)
    search_fields = ('cdate', 'mdate', 'user__email', 'customer__stripe_id', 'plan__label__key', 'plan__price', 'access', 'stripe_id',)

@admin.register(models.Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("cdate", "mdate", "customer", "subscription", "status", "plan", "stripe_id",)
    search_fields = ('cdate', 'mdate', 'user__email', 'customer__stripe_id', 'subscription__stripe_id', 'plan__label__key', 'stripe_id',)    