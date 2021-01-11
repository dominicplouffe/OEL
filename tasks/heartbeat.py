import os
import django

from oel.celery import app
from datetime import datetime, timedelta  
from api import models  
from tasks.notification import notification_check  
from api.common import schedule  
from tasks.ping import insert_failure

os.environ["DJANGO_SETTINGS_MODULE"] = 'oel.settings'
django.setup()


def process_heartbeat(push_key):
    heartbeat = models.Ping.objects.filter(
        push_key=push_key,
        active=True,
        heartbeat=True
    ).first()

    if not heartbeat:
        return False

    if not heartbeat.active:
        return False

    heartbeat.last_heartbeat = datetime.now()
    heartbeat.alive = True
    heartbeat.save()

    return True


@app.task
def dead_man_switch(heartbeat_id):

    heartbeat = models.Ping.objects.filter(
        pk=heartbeat_id,
        active=True,
        heartbeat=True
    ).first()

    if not heartbeat:
        return None, None

    now = datetime.utcnow()
    hour_date = datetime(
        now.year, now.month, now.day,
        now.hour, 0, 0
    )
    day_date = datetime(
        now.year, now.month, now.day
    )

    if heartbeat.alive:
        heartbeat.alive = False
        heartbeat.save()
        success = True
    else:
        success = False

    # Increment Result Hour
    result_hour = models.Result.objects.filter(
        ping=heartbeat,
        result_type='hour',
        result_date=hour_date
    ).first()

    if result_hour is None:
        result_hour = models.Result(
            ping=heartbeat,
            result_type='hour',
            result_date=hour_date,
            count=0,
            success=0,
            failure=0,
            total_time=0
        )

    result_hour.count += 1
    if success:
        result_hour.success += 1
    else:
        result_hour.failure += 1
    result_hour.save()

    # Increment Result Day
    result_day = models.Result.objects.filter(
        ping=heartbeat,
        result_type='day',
        result_date=day_date
    ).first()

    if result_day is None:
        result_day = models.Result(
            ping=heartbeat,
            result_type='day',
            result_date=day_date,
            count=0,
            success=0,
            failure=0,
            total_time=0
        )

    result_day.count += 1
    if success:
        result_day.success +=1
    else:
        result_day.failure += 1
    result_day.save()

    oncall_user = schedule.get_on_call_user(heartbeat.org)
    fail_res = insert_failure(heartbeat, "receive_alert", 500, "", oncall_user)

    return notification_check(
        success,
        heartbeat,
        result_day,
        fail_res,
        0,
        oncall_user
    )
