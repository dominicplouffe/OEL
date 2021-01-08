import os
import django

os.environ["DJANGO_SETTINGS_MODULE"] = 'oel.settings'
django.setup()


from api import models  # noqa


def update_pings():
    for ping in models.Ping.objects.all():
        alert = models.Alert(
            notification_type=ping.notification_type,
            incident_interval=ping.incident_interval,
            doc_link=ping.doc_link,
            active=ping.active,
            failure_count=ping.failure_count,
            callback_url=ping.callback_url,
            callback_username=ping.callback_userame,
            callback_password=ping.callback_password,
            notified_on=ping.notified_on,
            created_on=ping.created_on,
            updated_on=ping.updated_on,
            org=ping.org
        )

        alert.save()

        ping.alert = alert
        ping.save()

        for r in models.Result.objects.filter(ping=ping):
            r.alert = ping.alert
            r.save()

        for f in models.Failure.objects.filter(ping=ping):
            f.alert = ping.alert
            f.save()

        print(ping.id)


def insert_pongs():

    for ping in models.Ping.objects.filter(direction='push'):
        pong = models.Pong(
            org=ping.org,
            name=ping.name,
            active=ping.active,
            push_key=ping.push_key,
            created_on=ping.created_on,
            updated_on=ping.updated_on
        )

        alert = models.Alert(
            notification_type=ping.notification_type,
            incident_interval=ping.incident_interval,
            doc_link=ping.doc_link,
            active=ping.active,
            failure_count=ping.failure_count,
            callback_url=ping.callback_url,
            callback_username=ping.callback_userame,
            callback_password=ping.callback_password,
            notified_on=ping.notified_on,
            created_on=ping.created_on,
            updated_on=ping.updated_on,
            org=pong.org
        )

        alert.save()
        pong.alert = alert
        pong.save()

        for r in models.Result.objects.filter(ping=ping):
            r.alert = pong.alert
            r.save()

        for f in models.Failure.objects.filter(ping=ping):
            f.alert = pong.alert
            f.save()

        ping.delete()


if __name__ == '__main__':
    insert_pongs()

    update_pings()
