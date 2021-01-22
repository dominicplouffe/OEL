import os
import django

os.environ["DJANGO_SETTINGS_MODULE"] = 'oel.settings'
django.setup()

import requests  # noqa
from oel.celery import app  # noqa
from datetime import datetime  # noqa
from api import models  # noqa
from api.common import schedule  # noqa
from api.common import failure as fail_svc  # noqa
import json  # noqa
from api.common.result import process_result  # noqa


def insert_failure(alert, reason, status_code, content, org_user):

    create_fail = False
    fail = fail_svc.get_current_failure(alert)

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
            alert=alert,
            status_code=status_code,
            reason=reason,
            content=content[0:10000],
            notify_org_user=org_user
        )
        fail.save()

    return fail


def do_ping(
    endpoint, expected_str, expected_value, content_type, expected_status_code,
    failure=None, alert=None, auth=None, headers=None, oncall_user=None
):

    def insert_failure_tmp(ping, reason, status_code, content, org_user):
        pass

    if failure is None:
        failure = insert_failure_tmp
    success = True
    res = None
    reason = None
    fail_res = None
    try:
        res = requests.get(endpoint, headers=headers, auth=auth)
    except requests.exceptions.ConnectionError:
        success = False
        reason = 'connection_error'
        fail_res = failure(
            alert,
            reason,
            0,
            '',
            oncall_user
        )
    except requests.exceptions.ConnectTimeout:
        success = False
        reason = 'timeout_error'
        fail_res = failure(
            alert,
            reason,
            0,
            '',
            oncall_user
        )
    except BaseException:
        success = False
        reason = 'http_error'
        fail_res = failure(
            alert,
            reason,
            0,
            '',
            oncall_user
        )

    if res is not None:
        if res.status_code != expected_status_code:
            success = False
            reason = 'status_code'
            fail_res = failure(
                alert,
                reason,
                res.status_code,
                res.content.decode('utf-8'),
                oncall_user
            )
        elif content_type == "application/json":
            content = res.json()

            keys = expected_str.split('.')
            try:
                for k in keys:
                    content = content[k]

                content_value = '%s' % content
                content_value = content_value.lower()
                if content_value != expected_value.lower():
                    success = False
                    reason = 'value_error'
                    fail_res = failure(
                        alert,
                        reason,
                        res.status_code,
                        res.content.decode('utf-8'),
                        oncall_user
                    )

            except KeyError:
                success = False
                reason = 'key_error'
                fail_res = failure(
                    alert,
                    reason,
                    res.status_code,
                    res.content.decode('utf-8'),
                    oncall_user
                )
            except TypeError:
                success = False
                reason = 'key_error'
                fail_res = failure(
                    alert,
                    reason,
                    res.status_code,
                    res.content.decode('utf-8'),
                    oncall_user
                )
        else:
            content = res.content.decode('utf-8')

            if expected_value not in content:
                success = False
                reason = 'invalid_value'
                fail_res = failure(
                    alert,
                    reason,
                    res.status_code,
                    res.content.decode('utf-8'),
                    oncall_user
                )

    return res, reason, fail_res, success


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
        alert=ping.alert,
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

    diff = 0.00
    start_time = datetime.utcnow()
    res, reason, fail_res, success = do_ping(
        endpoint, ping.expected_string, ping.expected_value, ping.content_type,
        ping.status_code, auth=pass_info, headers=headers, alert=ping.alert,
        failure=failure, oncall_user=oncall_user)
    end_time = datetime.utcnow()

    if (not process_res):
        return res, reason

    diff = (end_time - start_time).total_seconds()

    return process_result(
        success,
        ping.alert,
        fail_res,
        ping.name,
        'ping',
        ping.id,
        oncall_user,
        diff=diff
    )


if __name__ == '__main__':

    process_ping(13)
