import pytz
import requests
from api.tools import mail, text
from api import models
from datetime import datetime
from api.common import schedule, failure


def notification_check(
    success,
    ping,
    result_day,
    fail_res,
    response_time,
    org_user
):

    notification_sent = False

    if success:
        if ping.failure_count > 0:
            ping.failure_count = 0

            if ping.notification_type == "team":
                if org_user.notification_type == "email":
                    ping.notified_on = datetime.utcnow()
                    mail.send_html_mail(
                        org_user.email_address,
                        "OnErrorLog Success : %s " % ping.name,
                        "ping_recovered.html",
                        {
                            'title': "OnErrorLog Success : %s " % ping.name
                        }
                    )
                else:
                    ping.notified_on = datetime.utcnow()
                    text.send_ping_success(org_user.phone_number, ping.name)
            else:
                send_callback(ping, fail_res, response_time, 'success')

            failure.recover_failure(ping)

    else:
        ping.failure_count += 1
        send_notification = False

        if ping.failure_count == ping.incident_interval:
            send_notification = True

        if send_notification:
            notification_sent = True
            if ping.notification_type == "team":
                if org_user.notification_type == "email":
                    ping.notified_on = datetime.utcnow()

                    template_name = "ping_failure.html"

                    if ping.direction == "push":
                        template_name = "pong_failure.html"

                    if ping.direction == "both":
                        template_name = "heartbeat_failure.html"

                    mail.send_html_mail(
                        org_user.email_address,
                        "OnErrorLog Failure : %s " % ping.name,
                        template_name,
                        {
                            'title': "OnErrorLog Failure : %s " % ping.name,
                            'doc_link': ping.doc_link
                        }
                    )
                else:
                    ping.notified_on = datetime.utcnow()

                    if ping.direction == "pull":
                        text.send_ping_failure(
                            org_user.phone_number, ping.name, ping.doc_link
                        )
                    else:
                        text.send_pong_failure(
                            org_user.phone_number, ping.name, ping.doc_link
                        )
            else:
                send_callback(ping, fail_res, response_time, 'failure')

    ping.save()

    return notification_sent


def send_callback(ping, fail_res, response_time, status):
    endpoint = ping.callback_url

    ping_headers = models.PingHeader.objects.filter(
        ping=ping,
        header_type='callback'
    )

    headers = {}
    for h in ping_headers:
        headers[h.key] = h.value

    pass_info = None
    if ping.callback_userame and ping.callback_password:
        pass_info = (
            ping.callback_userame,
            ping.callback_password
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
