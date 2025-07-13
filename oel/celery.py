import os
from celery import Celery
from django.conf import settings


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oel.settings")


app = Celery(
    "fancontent_app",
    include=[
        # 'api.common.email_notification',
        "tasks.ping",
        "tasks.schedule",
        "tasks.metric",
        "tasks.pong",
        "tasks.run",
    ],
    task_routes={"tasks.ping": {"queue": "ping"}},
)

app.config_from_object("django.conf:settings")
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

print("abc")
