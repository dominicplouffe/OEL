import pytz, json
import json
from datetime import datetime

import requests
from api import models
from api.common import failure
from api.tools import mail, text


def notification_check(
    success,
    alert,
    result_day,
    fail_res,
    response_time,
    org_user,
    direction,
    name
):

    notification_sent = False

    if success:
        if alert.failure_count > 0:
            alert.failure_count = 0

            if alert.notification_type == "team":
                if org_user.notification_type == "email":
                    alert.notified_on = datetime.utcnow()
                    mail.send_html_mail(
                        org_user.email_address,
                        "OnErrorLog Success : %s " % name,
                        "ping_recovered.html",
                        {
                            'title': "OnErrorLog Success : %s " % name
                        }
                    )
                else:
                    alert.notified_on = datetime.utcnow()
                    text.send_ping_success(org_user.phone_number, name)
            else:
                # TODO
                send_callback(alert, fail_res, response_time, 'success')

            failure.recover_failure(alert)

    else:
        alert.failure_count += 1
        send_notification = False

        if alert.failure_count == alert.incident_interval:
            send_notification = True

        if send_notification:
            notification_sent = True
            if alert.notification_type == "team":
                if org_user.notification_type == "email":
                    alert.notified_on = datetime.utcnow()

                    template_name = "ping_failure.html"
                    if ping.heartbeat:
                        template_name = "heartbeat_failure.html"
                    elif direction == "push":
                        template_name = "pong_failure.html"

                    mail.send_html_mail(
                        org_user.email_address,
                        "OnErrorLog Failure : %s " % name,
                        template_name,
                        {
                            'title': "OnErrorLog Failure : %s " % name,
                            'doc_link': alert.doc_link,
                            'failure_id': fail_res.id
                        }
                    )
                else:
                    alert.notified_on = datetime.utcnow()

                    if direction == "pull":
                        text.send_ping_failure(
                            org_user.phone_number, name,
                            alert.doc_link,
                            fail_res
                        )
                    elif ping.heartbeat:
                        text.send_heartbeat_failure(
                            org_user.phone_number, ping.name, ping.doc_link,
                            fail_res
                        )
                    else:
                        text.send_pong_failure(
                            org_user.phone_number,
                            name,
                            alert.doc_link,
                            fail_res
                        )
            else:
                # TODO
                send_callback(alert, fail_res, response_time, 'failure')

    alert.save()

    return notification_sent


def send_callback(alert, fail_res, response_time, status):
    endpoint = alert.callback_url

    ping_headers = models.PingHeader.objects.filter(
        alert=alert,
        header_type='callback'
    )

    headers = {}
    for h in ping_headers:
        headers[h.key] = h.value

    pass_info = None
    if alert.callback_userame and alert.callback_password:
        pass_info = (
            alert.callback_userame,
            alert.callback_password
        )

    try:
        requests.post(
            endpoint,
            data=json.dumps({
                'status_code': fail_res.status_code,
                'reason': fail_res.reason,
                'response_time': response_time,
                'status': status
            }),
            headers={'Content-Type': 'application/json'},
            auth=pass_info
        )
    except Exception as e:
        # If there's an error on the customer's callback, we ignore at the
        # moment.  We need to handle this somehow.
        print(e)
        pass
