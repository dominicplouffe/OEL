from django.core.mail import EmailMessage
from django.core.mail import send_mail as django_send
from django.template.loader import get_template
from email.header import Header
from email.utils import formataddr


def send_mail(email, subject, body):
    # template = get_template(template)
    # message = EmailMessage(subject, template.render(
    #     context), to=[email])
    # body = "There was an error in your ping check"

    message = EmailMessage(
        subject,
        body,
        to=[email]
    )
    message.send()


def send_html_mail(email, subject, template, context):
    template = get_template(template)

    html_message = template.render(context)
    message = ""

    from_email = formataddr(
        (
            str(Header('OnErrorLog Notification', 'utf-8')),
            'notification@onerrorlog.com'
        )
    )

    django_send(
        subject,
        message,
        from_email,
        [email],
        html_message=html_message
    )


def send_test_email(to):
    message = EmailMessage('OnErrorLog: Test Email', 'Test Email', to=[to])
    message.send()


def send_confirmation_email(to_email, code, host):

    send_mail(
        to_email,
        'onErrorLog: Please Confirm Your Email Address',
        """onErrorLog: Please Confirm Your Email Address
        
        Your confirmation code is: %s""" % (code)
    )


def send_invite_email(to_email, host, code):

    url = '%s/auth/accept-invite?code=%s' % (host, code)

    send_mail(
        to_email,
        'onErrorLog: You have been invite',
        """You have been invited to onErrorLog

        Click the link below to accept your
         invitation and to complete your profile.

         %s""" % url
    )


def send_going_oncall_email(to_email):

    send_mail(
        to_email,
        "onErrorLog: You are going on call",
        "Just letting you know that you are going on call for the next 7 days"
    )
