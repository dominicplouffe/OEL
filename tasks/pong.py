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


def _get_interval_value(trigger):
    interval_value = trigger.interval_value
    if trigger.unit == "minutes":
        interval_value = trigger.interval_value * 60
    elif trigger.unit == "days":
        interval_value = trigger.interval_value * 60 * 24

    return interval_value


def runs_less_than(trigger, diff, pong, oncall_user):

    interval_value = _get_interval_value(trigger)

    if diff < interval_value:
        reason = 'runs_less_than'

        fail_res = insert_failure(
            pong.alert,
            reason,
            500,
            "Expected Seconds: %s - Num Seconds: %.2f" % (
                interval_value,
                diff
            ),
            oncall_user
        )

        return fail_res

    return None


def runs_more_than(trigger, diff, pong, oncall_user):

    interval_value = _get_interval_value(trigger)

    if diff > interval_value:
        reason = 'runs_more_than'

        fail_res = insert_failure(
            pong.alert,
            reason,
            500,
            "Expected Seconds: %s - Num Seconds: %.2f" % (
                interval_value,
                diff
            ),
            oncall_user
        )

        return fail_res

    return None


def start_not_triggered_in(trigger, pong, oncall_user):
    if not pong.last_start_on:
        return

    if pong.cron_desc:
        if not cron.is_now_ok(pong.cron_desc):
            return

    diff = (datetime.now(pytz.UTC) - pong.last_start_on).total_seconds() - 60

    interval_value = _get_interval_value(trigger)

    if (diff > interval_value):

        reason = 'start_not_triggered'

        fail_res = insert_failure(
            pong.alert,
            reason,
            500,
            "Pong Start On last triggered on: %s - Num Seconds: %.2f" % (
                pong.last_start_on,
                diff
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

    diff = (datetime.now(pytz.UTC) - pong.last_start_on).total_seconds() - 60

    print('complete_not_triggered_in: %s' % diff)

    interval_value = _get_interval_value(trigger)

    if (diff > interval_value):

        reason = 'comp_not_triggered'

        fail_res = insert_failure(
            pong.alert,
            reason,
            500,
            "Pong Completed On Last triggered on: %s - Num Seconds: %.2f" % (
                pong.last_start_on,
                diff
            ),
            oncall_user
        )

        return fail_res

    return None


def heartbeat_triggered(trigger, pong, oncall_user):
    reason = 'heartbeat_triggered'

    fail_res = insert_failure(
        pong.alert,
        reason,
        500,
        "Hearbeat was triggered from your task",
        oncall_user
    )

    return fail_res


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
    success = True
    fail_res = None
    sent = False

    if pos == 'start':
        pong.last_start_on = datetime.now(pytz.UTC)
    elif pos == 'fail':
        try:
            trigger = models.PongTrigger.objects.get(
                pong_id=pong.id,
                trigger_type='heartbeat_triggered'
            )
            fail_res = heartbeat_triggered(trigger, pong, oncall_user)

            success = False

            sent = process_result(
                success,
                pong.alert,
                fail_res,
                pong.name,
                'pong',
                pong.id,
                oncall_user
            )

        except models.PongTrigger.DoesNotExist:
            pass

    elif pos == 'end':
        pong.last_complete_on = datetime.now(pytz.UTC)

        if pong.last_start_check is None or (
            pong.last_start_on != pong.last_start_check
        ):
            triggers = models.PongTrigger.objects.filter(pong_id=pong.id)

            trigger_actions = {
                'runs_more_than': runs_more_than,
                'runs_less_than': runs_less_than
            }

            # Get diff
            diff = datetime.now(pytz.UTC) - pong.last_start_on

            # Insert the metrics
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

            # Set Pong last start check date
            pong.last_start_check = pong.last_start_on

            perf_trigger = False
            for trigger in triggers:
                if trigger.trigger_type not in trigger_actions:
                    continue

                perf_trigger = True
                fail_res = trigger_actions[trigger.trigger_type](
                    trigger,
                    diff.total_seconds(),
                    pong,
                    oncall_user
                )

                if fail_res:
                    success = False
                    break

            if perf_trigger:
                sent = process_result(
                    success,
                    pong.alert,
                    fail_res,
                    pong.name,
                    'pong',
                    pong.id,
                    oncall_user,
                    diff=diff.total_seconds()
                )

    pong.save()

    return {
        'sent': sent,
        'pos': pos
    }


@app.task
def process_pong_alert(pong_id):

    triggers = models.PongTrigger.objects.filter(pong_id=pong_id)
    pong = models.Pong.objects.get(id=pong_id)
    oncall_user = schedule.get_on_call_user(pong.org)

    if not pong.active:
        return

    trigger_actions = {
        'start_not_triggered_in': start_not_triggered_in,
        'complete_not_triggered_in': complete_not_triggered_in
    }

    fail_res = None

    for trigger in triggers:
        if trigger.trigger_type not in trigger_actions:
            continue

        fail_res = trigger_actions[trigger.trigger_type](
            trigger,
            pong,
            oncall_user
        )

        if fail_res:
            break

    process_result(
        fail_res is None,
        pong.alert,
        fail_res,
        pong.name,
        'pong',
        pong.id,
        oncall_user
    )


if __name__ == '__main__':

    process_pong_alert(3)
