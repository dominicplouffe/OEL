from oel.settings import TWILIO_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE
from twilio.rest import Client


def send_text_message(to, body):
    client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

    client.messages.create(from_=TWILIO_PHONE, to=to, body=body)


def send_going_offcall(phone_number):
    send_text_message(
        phone_number,
        "OnErrorLog: Just letting you know that your on-call assistance"
        " is no longer needed",
    )


def send_going_oncall(phone_number):
    send_text_message(
        phone_number, "OnErrorLog: Just letting you know that you are going on call"
    )


def send_ping_success(phone_number, ping_name):

    body = "OnErrorLog Success : %s - " % ping_name
    body += "Your ping has been recovered, everything is back to normal."
    send_text_message(phone_number, body)


def send_failure(phone_number, ping_name, doc_link, fail_res):

    body = "OnErrorLog Failure : %s - Your monitor has triggered" % ping_name
    body += " enpoint. Please login to onErrorLog and check it out."
    body += " - https://app.onerrorlog.com/failure/%s/" % fail_res.id

    if doc_link and doc_link.startswith("http"):
        body += " - Documentation: %s" % doc_link

    send_text_message(phone_number, body)
