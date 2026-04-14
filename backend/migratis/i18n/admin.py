from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from . import models

class TranslationNameSpaceResource(resources.ModelResource):

    class Meta:
        model = models.TranslationNameSpace

class TranslationKeyResource(resources.ModelResource):

    class Meta:
        model = models.TranslationKey

class TranslationTextResource(resources.ModelResource):

    class Meta:
        model = models.TranslationText

@admin.register(models.TranslationText)
class TranslationTextOnlyAdmin(ImportExportModelAdmin):
    resource_class = TranslationTextResource

class TranslationTextAdmin(admin.TabularInline):
    model = models.TranslationText



@admin.register(models.TranslationKey)
class TranslationKeyAdmin(ImportExportModelAdmin):
    list_display = ('key',)
    resource_class = TranslationKeyResource
    search_fields = ('key', 'ns__ns',)
    inlines = [
        TranslationTextAdmin
    ]

@admin.register(models.TranslationNameSpace)
class TranslationNameSpaceAdmin(ImportExportModelAdmin):
    list_display = ('ns',) 
    resource_class = TranslationNameSpaceResource
    search_fields = ('ns',)



   