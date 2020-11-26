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

logger = logging.getLogger(__name__)


@app.task
def reschedule():

    date = datetime.utcnow()

    if date.weekday() != 0:
        return

    for org in models.Org.objects.all():

        new_week = org.week + 1

        if new_week > models.OrgUser.objects.filter(
            org=org, is_oncall=True, active=True
        ).count():

            new_week = 1

        org.week = new_week
        org.save()

        try:
            sch = models.Schedule.objects.get(org=org, order=new_week)
            usr = sch.org_user
        except models.Schedule.DoesNotExist:
            logger.error('Could not find any users: %s' % org.name)
            continue

        logger.info('Sending notification to: %s' % usr.email_address)
        if usr.notification_type == "email":
            mail.send_going_oncall_email(usr.email_address)
        else:
            text.sent_text_message(
                usr.phone_number,
                "Just letting you know that you are going on call "
                "for the next 7 days"
            )


if __name__ == '__main__':

    reschedule()
