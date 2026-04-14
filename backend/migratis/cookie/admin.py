from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from . import models


class CookieResource(resources.ModelResource):

    class Meta:
        model = models.Cookie

@admin.register(models.Cookie)
class CookieAdmin(ImportExportModelAdmin):
    list_display = ('name', 'provider', 'description')
    resource_class = CookieResource
    search_fields = ('name', 'provider', 'description')