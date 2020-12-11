import os
import django

os.environ["DJANGO_SETTINGS_MODULE"] = 'oel.settings'
django.setup()

import requests  # noqa
from oel.celery import app  # noqa
from datetime import datetime  # noqa
from api import models  # noqa
from tasks.notification import notification_check  # noqa
from api.common import schedule  # noqa
from api.common import failure as fail_svc  # noqa
import json  # noqa


def insert_failure(ping, reason, status_code, content, org_user):

    create_fail = False
    fail = fail_svc.get_current_failure(ping)

    if not fail:
        create_fail = True
    else:
        if fail.ignored_on is not None:
            create_fail = True
        if fail.fixed_on is not None:
            create_fail = True
        if fail.recovered_on is not None:
            create_fail = True

    if create_fail:
        fail = models.Failure(
            ping=ping,
            status_code=status_code,
            reason=reason,
            content=content[0:10000],
            notify_org_user=org_user
        )
        fail.save()

    return fail


@app.task
def process_ping(ping_id, failure=insert_failure, process_res=True):

    if process_res:
        ping = models.Ping.objects.filter(
            pk=ping_id,
            active=True
        ).first()
    else:
        ping = models.Ping.objects.filter(
            pk=ping_id
        ).first()

    if not ping:
        return None, None

    if not ping.active and process_res:
        return None, None

    oncall_user = schedule.get_on_call_user(ping.org)

    if not oncall_user:
        return None, None

    endpoint = ping.endpoint

    ping_headers = models.PingHeader.objects.filter(
        ping=ping,
        header_type='endpoint'
    )

    headers = {}
    for h in ping_headers:
        headers[h.key] = h.value

    pass_info = None
    if ping.endpoint_username and ping.endpoint_password:
        pass_info = (
            ping.endpoint_username,
            ping.endpoint_password
        )

    success = True
    res = None
    reason = None
    start_time = datetime.utcnow()
    fail_res = None
    diff = 0.00
    try:
        res = requests.get(endpoint, headers=headers, auth=pass_info)
    except requests.exceptions.ConnectionError:
        success = False
        reason = 'connection_error'
        fail_res = failure(
            ping,
            reason,
            0,
            '',
            oncall_user
        )
    except requests.exceptions.ConnectTimeout:
        success = False
        reason = 'timeout_error'
        fail_res = failure(
            ping,
            reason,
            0,
            '',
            oncall_user
        )
    except:
        success = False
        reason = 'http_error'
        fail_res = failure(
            ping,
            reason,
            0,
            '',
            oncall_user
        )
    end_time = datetime.utcnow()

    if res is not None:
        if res.status_code != ping.status_code:
            success = False
            reason = 'status_code'
            fail_res = failure(
                ping,
                reason,
                res.status_code,
                res.content.decode('utf-8'),
                oncall_user
            )
        elif ping.content_type == "application/json":
            content = res.json()

            keys = ping.expected_string.split('.')
            try:
                for k in keys:
                    content = content[k]

                content_value = '%s' % content
                content_value = content_value.lower()
                if content_value != ping.expected_value.lower():
                    reason = 'value_error'
                    fail_res = failure(
                        ping,
                        reason,
                        res.status_code,
                        res.content.decode('utf-8'),
                        oncall_user
                    )

            except KeyError:
                success = False
                reason = 'key_error'
                fail_res = failure(
                    ping,
                    reason,
                    res.status_code,
                    res.content.decode('utf-8'),
                    oncall_user
                )
            except TypeError:
                success = False
                reason = 'key_error'
                fail_res = failure(
                    ping,
                    reason,
                    res.status_code,
                    res.content.decode('utf-8'),
                    oncall_user
                )
        else:
            content = res.content.decode('utf-8')

            if ping.expected_value not in content:
                success = False
                reason = 'invalid_value'
                fail_res = failure(
                    ping,
                    reason,
                    res.status_code,
                    res.content.decode('utf-8'),
                    oncall_user
                )

    diff = (end_time - start_time).total_seconds()

    now = datetime.utcnow()
    hour_date = datetime(
        now.year, now.month, now.day,
        now.hour, 0, 0
    )
    day_date = datetime(
        now.year, now.month, now.day
    )

    if process_res:

        # Increment Result Hour
        result_hour = models.Result.objects.filter(
            ping=ping,
            result_type='hour',
            result_date=hour_date
        ).first()

        if result_hour is None:
            result_hour = models.Result(
                ping=ping,
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

        result_hour.total_time += diff
        result_hour.save()

        # Increment Result Day
        result_day = models.Result.objects.filter(
            ping=ping,
            result_type='day',
            result_date=day_date
        ).first()

        if result_day is None:
            result_day = models.Result(
                ping=ping,
                result_type='day',
                result_date=day_date,
                count=0,
                success=0,
                failure=0,
                total_time=0
            )

        result_day.count += 1
        if success:
            result_day.success += 1
        else:
            result_day.failure += 1

        result_day.total_time += diff
        result_day.save()

        notification_check(
            success, ping, result_day, fail_res, diff, oncall_user
        )
    else:

        return res, reason


if __name__ == '__main__':

    process_ping(1)
