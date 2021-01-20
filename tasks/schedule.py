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
from api.common.schedule import get_on_call_user  # noqa
from datetime import datetime, timedelta  # noqa

logger = logging.getLogger(__name__)


@app.task
def reschedule():

    date = datetime.utcnow()

    if date.weekday() != 0:
        return

    yesterday = datetime.utcnow() - timedelta(days=1)
    today = datetime.utcnow()

    for org in models.Org.objects.all():

        # Tell previous user that they are going off call
        try:
            usr = get_on_call_user(org, current_date=yesterday)
        except models.Schedule.DoesNotExist:
            logger.error('Could not find any users: %s' % org.name)
            continue

        logger.info('Sending notification to: %s' % usr.email_address)
        if usr.notification_type == "email":
            mail.send_going_oncall_email(usr.email_address)
        else:
            text.send_going_offcall(usr.phone_number)

        # Increament the week
        new_week = org.week + 1

        if new_week > models.OrgUser.objects.filter(
            org=org, is_oncall=True, active=True
        ).count():
            new_week = 1

        org.week = new_week
        org.save()

        # Tell new user that they are going on call.
        try:
            usr = get_on_call_user(org, current_date=today)
        except models.Schedule.DoesNotExist:
            logger.error('Could not find any users: %s' % org.name)
            continue

        logger.info('Sending notification to: %s' % usr.email_address)
        if usr.notification_type == "email":
            mail.send_going_oncall_email(usr.email_address)
        else:
            text.send_going_oncall(usr.phone_number)


if __name__ == '__main__':

    reschedule()
