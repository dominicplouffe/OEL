from oel.settings import TWILIO_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE
from twilio.rest import Client


def sent_text_message(to, body):
    client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

    message = client.messages.create(
        from_=TWILIO_PHONE,
        to=to,
        body=body
    )


def send_going_offcall(phone_number):

    sent_text_message(
        phone_number,
        "Just letting you know that your on-call assistance"
        " is no longer needed"
    )


def send_going_oncall(phone_number):
    sent_text_message(
        phone_number,
        "Just letting you know that you are going on call "
        "for the next 7 days"
    )


def send_ping_success(phone_number, ping_name):

    body = "OnErrorLog Success : %s - Your ping has been recovered, "
    body += "everything is back to normal." % ping_name
    sent_text_message(
        phone_number,
        body
    )


def send_ping_failure(phone_number, ping_name, doc_link, fail_res):

    body = "OnErrorLog Failure : %s - We could not ping your" % ping_name
    body += " enpoint. Please login to onErrorLog and check it out."
    body += " - https://app.onerrorlog.com/failure/%s/" % fail_res.id

    if doc_link and doc_link.startswith('http'):
        body += " - Documentation: %s" % doc_link

    sent_text_message(
        phone_number,
        body
    )


def send_pong_failure(phone_number, ping_name, doc_link, fail_res):

    body = "OnErrorLog Failure : %s - We received a notification. " % ping_name
    body += "One of your Pongs seems to be down.  "
    body += "Please login to onErrorLog and check it out."

    body += "\n\nhttps://app.onerrorlog.com/failure/%s/" % fail_res.id

    if doc_link and doc_link.startswith('http'):
        body += "\n\nDocumentation: %s" % doc_link

    sent_text_message(
        phone_number,
        body
    )
