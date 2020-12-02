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
            'dominic@dplouffe.ca'
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

    send_html_mail(
        to_email,
        'onErrorLog: Please Confirm Your Email Address',
        'email_confirmation.html',
        {
            'title': 'onErrorLog: Email Confirmation',
            'code': code
        }
    )


def send_invite_email(to_email, host, code):

    url = '%s/auth/accept-invite?code=%s' % (host, code)

    send_html_mail(
        to_email,
        'onErrorLog: You have been invited',
        'invite.html',
        {
            'title': 'onErrorLog: You have been invited',
            'url': url
        }
    )


def send_going_oncall_email(to_email):

    send_html_mail(
        to_email,
        'onErrorLog: You are going on call',
        'going_oncall.html',
        {
            'title': 'onErrorLog: You are going on call'
        }
    )


def send_going_offcall_email(to_email):

    send_html_mail(
        to_email,
        'onErrorLog: You are going off call',
        'going_offcall.html',
        {
            'title': 'onErrorLog: You are going off call'
        }
    )
