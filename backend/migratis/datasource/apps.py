from django.apps import AppConfig


class DataSourceConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'migratis.datasource'
    label = 'datasource'
    verbose_name = 'External data sources'
