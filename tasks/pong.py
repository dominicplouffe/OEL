import os
import django

os.environ["DJANGO_SETTINGS_MODULE"] = 'oel.settings'
django.setup()

import pytz  # noqa
from api import models  # noqa
from api.common import schedule  # noqa
from tasks.ping import insert_failure  # noqa
from api.common.result import process_result  # noqa
from datetime import datetime  # noqa
from oel.celery import app  # noqa
from api.common import cron  # noqa


def process_pong(pos, push_key):

    pong = models.Pong.objects.filter(
        push_key=push_key,
        active=True
    ).first()

    if not pong:
        return False

    if not pong.active:
        return False

    oncall_user = schedule.get_on_call_user(pong.org)
    reason = 'receive_alert'
    success = True
    fail_res = None

    if pos == 'start':
        pong.last_start_on = datetime.utcnow()
    elif pos == 'end':
        pong.last_complete_on = datetime.utcnow()

        if pong.last_start_check is None or (
            pong.last_start_on != pong.last_start_check
        ):
            # Insert the metrics
            diff = datetime.now(pytz.UTC) - pong.last_start_on
            metrics = {
                'task_time': diff.total_seconds()
            }
            tags = {
                'category': 'pong',
                'id': pong.id
            }
            m = models.Metric(
                org=pong.org,
                metrics=metrics,
                tags=tags
            )
            m.save()
            pong.last_start_check = pong.last_start_on

            process_result(
                False,
                pong.alert,
                fail_res,
                pong.name,
                oncall_user,
                diff=diff.total_seconds()
            )

    pong.save()

    return {
        'sent': True,
        'pos': pos
    }


@app.task
def process_pong_alert(pong_id):

    triggers = models.PongTrigger.objects.filter(pong_id=pong_id)
    pong = models.Pong.objects.get(id=pong_id)
    oncall_user = schedule.get_on_call_user(pong.org)

    for trigger in triggers:
        fail_res = trigger_actions[trigger.trigger_type](
            trigger,
            pong,
            oncall_user
        )

        process_result(
            fail_res == None,
            pong.alert,
            fail_res,
            pong.name,
            oncall_user
        )


def start_not_triggered_in(trigger, pong, oncall_user):
    if not pong.last_start_on:
        return

    if pong.cron_desc:
        if not cron.is_now_ok(pong.cron_desc):
            return

    diff = datetime.now(pytz.UTC) - pong.last_start_on

    interval_value = trigger.interval_value
    if trigger.unit == "minutes":
        trigger_value = trigger_value * 60
    elif trigger.unit == "days":
        trigger_value = trigger_value * 60 * 24

    if (diff.total_seconds() > interval_value):

        reason = 'start_not_triggered'

        fail_res = insert_failure(
            pong.alert,
            reason,
            500,
            "Pong Start On last triggered on: %s - Num Seconds: %.2f" % (
                pong.last_start_on,
                diff.total_seconds()
            ),
            oncall_user
        )

        return fail_res

    return None


def complete_not_triggered_in(trigger, pong, oncall_user):

    if not pong.last_complete_on:
        return

    if pong.cron_desc:
        if not cron.is_now_ok(pong.cron_desc):
            return

    diff = datetime.now(pytz.UTC) - pong.last_complete_on

    print('complete_not_triggered_in: %s' % diff)

    interval_value = trigger.interval_value
    if trigger.unit == "minutes":
        trigger_value = trigger_value * 60
    elif trigger.unit == "days":
        trigger_value = trigger_value * 60 * 24

    if (diff.total_seconds() > interval_value):

        reason = 'comp_not_triggered'

        fail_res = insert_failure(
            pong.alert,
            reason,
            500,
            "Pong Completed On Last triggered on: %s - Num Seconds: %.2f" % (
                pong.last_start_on,
                diff.total_seconds()
            ),
            oncall_user
        )

        return fail_res

    return None


trigger_actions = {
    'start_not_triggered_in': start_not_triggered_in,
    'complete_not_triggered_in': complete_not_triggered_in
}


if __name__ == '__main__':

    process_pong_alert(3)
