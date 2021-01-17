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


def process_pong(pos, push_key):

    # process_pong_alert(2)
    pong = models.Pong.objects.filter(
        push_key=push_key,
        active=True
    ).first()

    if not pong:
        return False

    if not pong.active:
        return False

    reason = 'receive_alert'

    if pos == 'start':
        pong.last_start_on = datetime.utcnow()
    elif pos == 'end':
        pong.last_complete_on = datetime.utcnow()

    pong.save()

    return {
        'sent': True,
        'pos': pos
    }

    # oncall_user = schedule.get_on_call_user(pong.org)

    # fail_res = insert_failure(
    #     pong.alert,
    #     "receive_alert",
    #     500,
    #     "",
    #     oncall_user
    # )

    # return process_result(
    #     False,
    #     pong.alert,
    #     fail_res,
    #     pong.name,
    #     oncall_user
    # )
    return True


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

    diff = datetime.now(pytz.UTC) - pong.last_start_on

    if (diff.total_seconds() > trigger.interval_value):

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
    else:
        metrics = {
            'task_time': diff
        }
        tags = {
            'category': 'pong'
        }
        m = Metric(
            org=pong.org,
            metric=metrics,
            tags=tags
        )
        m.save()

    return None


def complete_not_triggered_in(trigger, pong, oncall_user):

    if not pong.last_complete_on:
        return

    diff = datetime.now(pytz.UTC) - pong.last_complete_on

    if (diff.total_seconds() > trigger.interval_value):

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
