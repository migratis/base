from django.apps import AppConfig

class SubscriptionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'migratis.subscription'

    def ready(self):
        # Register subscription checkout + grant + lifecycle handlers with the
        # unified billing engine.
        from migratis.subscription.billing import register as _register_billing
        _register_billing()

  
