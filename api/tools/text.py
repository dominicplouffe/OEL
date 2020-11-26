from oel.settings import TWILIO_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE
from twilio.rest import Client


def sent_text_message(to, body):
    client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

    message = client.messages.create(
        from_=TWILIO_PHONE,
        to=to,
        body=body
    )
