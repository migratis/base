from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from . import models


class CookieResource(resources.ModelResource):

    class Meta:
        model = models.Cookie


@admin.register(models.Cookie)
class CookieAdmin(ImportExportModelAdmin):
    list_display = (
        'name', 'storage', 'category', 'retention', 'provider', 'description',
    )
    list_filter = ('category', 'storage', 'provider')
    resource_class = CookieResource
    search_fields = ('name', 'provider', 'description__key')

    @admin.display(description='Retention')
    def retention(self, obj):
        if obj.retention_unit in models.Cookie.UNCOUNTED_RETENTION_UNITS:
            return obj.get_retention_unit_display()
        return f'{obj.retention_value} {obj.get_retention_unit_display().lower()}'
