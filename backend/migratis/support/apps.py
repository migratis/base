from django.apps import AppConfig

class SupportConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'migratis.support'

    def ready(self):
        import migratis.support.signals
