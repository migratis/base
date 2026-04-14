from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.admin.widgets import FilteredSelectMultiple    
from django.contrib.auth.models import Group
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from . import models

User = get_user_model()

# Create ModelForm based on the Group model.
class GroupAdminForm(forms.ModelForm):
    class Meta:
        model = Group
        exclude = []

    # Add the users field.
    users = forms.ModelMultipleChoiceField(
         queryset=User.objects.all(), 
         required=False,
         # Use the pretty 'filter_horizontal widget'.
         widget=FilteredSelectMultiple('users', False)
    )

    def __init__(self, *args, **kwargs):
        # Do the normal form initialisation.
        super(GroupAdminForm, self).__init__(*args, **kwargs)
        # If it is an existing group (saved objects have a pk).
        if self.instance.pk:
            # Populate the users field with the current Group users.
            self.fields['users'].initial = self.instance.user_set.all()

    def save_m2m(self):
        # Add the users to the Group.
        self.instance.user_set.set(self.cleaned_data['users'])

    def save(self, *args, **kwargs):
        # Default save
        instance = super(GroupAdminForm, self).save()
        # Save many-to-many data
        self.save_m2m()
        return instance
    
# Unregister the original Group admin.
admin.site.unregister(Group)

class GroupResource(resources.ModelResource):

    class Meta:
        model = Group

# Create a new Group admin.
class GroupAdmin(ImportExportModelAdmin):
    model=Group
    # Use our custom form.
    form = GroupAdminForm
    # Filter permissions horizontal as well.
    filter_horizontal = ['permissions']
    resource_class = GroupResource

# Register the new Group ModelAdmin.
admin.site.register(Group, GroupAdmin)    

class UserResource(resources.ModelResource):

    class Meta:
        model = models.User

@admin.register(models.User)
class UserAdmin(ImportExportModelAdmin):
    model = models.User
    list_display = ('email', 'first_name', 'last_name', 'language', 'is_staff', 'is_active', 'professional', 'deleted', 'cdate', 'mdate')
    list_filter = ('is_staff', 'is_active', 'professional')
    fieldsets = (
        (None, {'fields': ('email', 'first_name', 'last_name', 'language', 'birthdate', 'address', 'zipcode', 'city', 'country', 'professional', 'company', 'taxnumber', 'old_passwords', 'deleted',)}),
        ('Permissions', {'fields': ('is_staff', 'is_active')}),
    )
    search_fields = ('email', 'cdate', 'mdate')
    ordering = ('email',)
    resource_class = UserResource





