import os
import django

os.environ["DJANGO_SETTINGS_MODULE"] = 'oel.settings'
django.setup()

import requests  # noqa
from api import models  # noqa
from datetime import datetime  # noqa
from api.tools import mail, text  # noqa
from oel.celery import app  # noqa
import logging  # noqa
from api.common.metrics import notification  # noqa


@app.task
def process_metrics():

    conditions = models.MetricCondition.objects.filter(
        active=True
    )

    for condition in conditions:
        notification_sent = notification.check_notification_rule(
            condition,
            send_notification=True
        )


if __name__ == '__main__':
    process_metrics()
