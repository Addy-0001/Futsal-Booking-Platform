from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.common"

    def ready(self):
        # Backport Django's Python 3.14 template-context copy fix (ticket #35844).
        from .compat import apply

        apply()

        # Turn the admin home into a stats dashboard.
        from .admin_dashboard import install

        install()
