from django.contrib import admin

from .models import DerivationRun


@admin.register(DerivationRun)
class DerivationRunAdmin(admin.ModelAdmin):
    """The run log (SCOPE_calculated_tables.md §6.5) — read-only: it is the
    record of what a calculation said on a given day."""
    list_display = ("started_at", "application_key", "derivation_key", "anchor_key",
                    "host", "trigger", "status", "error_code", "total")
    list_filter = ("host", "status", "trigger")
    search_fields = ("application_key", "derivation_key", "anchor_key", "error_code")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
