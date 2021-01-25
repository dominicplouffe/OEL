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
import pytz  # noqa
from api.common.schedule import get_on_call_user  # noqa
from datetime import datetime, timedelta  # noqa

logger = logging.getLogger(__name__)


@app.task
def reschedule(send_anyways=False):

    for org in models.Org.objects.all():
        do_schedule(org, send_anyways=send_anyways)


def do_schedule(org, send_anyways=False):

    yesterday = datetime.now(pytz.UTC) - timedelta(days=1)
    today = datetime.now(pytz.UTC)

    # Check if there's an override for today
    override_today = models.ScheduleOverride.objects.filter(
        start_date__lte=today, end_date__gte=today, org=org
    )
    override_yesterday = models.ScheduleOverride.objects.filter(
        start_date__lte=yesterday, end_date__gte=yesterday, org=org
    )

    if not send_anyways:
        if today.weekday() != 0 and override_today.count() == 0 and \
                override_yesterday.count() == 0:
            return

    # Tell previous user that they are going off call
    try:
        usr = get_on_call_user(org, current_date=yesterday)
    except models.Schedule.DoesNotExist:
        logger.error('Could not find any users: %s' % org.name)
        return

    logger.info('Sending notification to: %s' % usr.email_address)
    if usr.notification_type == "email":
        mail.send_going_offcall_email(usr.email_address)
    else:
        text.send_going_offcall(usr.phone_number)

    if today.weekday() == 0:
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
        return

    logger.info('Sending notification to: %s' % usr.email_address)
    if usr.notification_type == "email":
        mail.send_going_oncall_email(usr.email_address)
    else:
        text.send_going_oncall(usr.phone_number)


if __name__ == '__main__':
    reschedule()
