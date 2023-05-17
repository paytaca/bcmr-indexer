from django.apps import AppConfig


class BcmrMainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bcmr_main'

    def ready(self):
        import bcmr_main.signals
