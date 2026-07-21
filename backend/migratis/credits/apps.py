from django.apps import AppConfig


class CreditsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'migratis.credits'

    def ready(self):
        # Register the credit checkout + grant + invoice handlers with the
        # unified stripe_payment billing engine.
        from migratis.credits.billing import register as _register_billing
        _register_billing()
