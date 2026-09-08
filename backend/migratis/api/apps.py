from django.apps import AppConfig

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'migratis.api'

    def ready(self):
        # Registers the framework's own system checks. `api` is always in
        # INSTALLED_APPS, so this is the one place a check about the whole
        # migratis/ tree is guaranteed to be registered from.
        from . import checks  # noqa: F401


