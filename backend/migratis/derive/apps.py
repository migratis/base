from django.apps import AppConfig


class DeriveConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'migratis.derive'
    label = 'derive'
    verbose_name = 'Calculated tables'
