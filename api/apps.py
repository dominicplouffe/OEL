from django.apps import AppConfig


class ApiConfig(AppConfig):
    name = "api"

    def ready(self):
        from oel.startup import setup_oel
        import os

        if (
            os.environ.get("RUN_MAIN", None) != "true"
        ):  # Prevent double run in dev server
            return
        setup_oel()
