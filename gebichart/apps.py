from django.apps import AppConfig


class GebichartConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gebichart'

    def ready(self):
        from . import signals  # noqa: F401
