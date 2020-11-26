import pytz
import requests
from api.tools import mail, text
from api import models
from datetime import datetime
from api.common import schedule


def notification_check(
    success, ping, result_day, fail_res, response_time, org_user
):

    notification_sent = False

    if success:
        if ping.failure_count > 0:
            ping.failure_count = 0
            if ping.notification_type == "team":

                if org_user.notification_type == "email":
                    ping.notified_on = datetime.utcnow()
                    mail.send_mail(
                        org_user.email_address,
                        "OnErrorLog Success : %s" % ping.name,
                        "Your ping has been recovered, everything is"
                        " back to normal"
                    )
                else:
                    ping.notified_on = datetime.utcnow()

                    text.sent_text_message(
                        org_user.phone_number,
                        "OnErrorLog Success : %s - "
                        "Your ping has been recovered, everything is"
                        " back to normal" % ping.name
                    )
            else:
                send_callback(ping, fail_res, response_time, 'success')

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
                    mail.send_mail(
                        org_user.email_address,
                        "OnErrorLog Failure : %s " % ping.name,
                        "We could not ping your enpoint.  Please login to"
                        "onErrorLog and check it out"
                    )
                else:
                    ping.notified_on = datetime.utcnow()

                    text.sent_text_message(
                        org_user.phone_number,
                        "OnErrorLog Failure : %s - "
                        "We could not ping your enpoint.  Please login to"
                        "onErrorLog and check it out" % ping.name
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
