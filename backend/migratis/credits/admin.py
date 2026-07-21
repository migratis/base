from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import CreditBalance, CreditCost


class CreditBalanceResource(resources.ModelResource):
    class Meta:
        model = CreditBalance


class CreditCostResource(resources.ModelResource):
    class Meta:
        model = CreditCost


@admin.register(CreditBalance)
class CreditBalanceAdmin(ImportExportModelAdmin):
    list_display  = ('user', 'credits', 'cdate', 'mdate')
    search_fields = ('user__email',)
    resource_class = CreditBalanceResource


@admin.register(CreditCost)
class CreditCostAdmin(ImportExportModelAdmin):
    list_display  = ('operation', 'credits')
    ordering      = ('operation',)
    fields        = ('operation', 'credits')
    readonly_fields = ('operation',)
    resource_class = CreditCostResource
