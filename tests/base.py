import random
import factory
from api import models
from django.test import TestCase
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from api.common import schedule


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        abstract = False

    password = factory.PostGenerationMethodCall(
        'set_password', '12345'
    )


class OrgFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = models.Org
        abstract = False

    name = factory.Faker('company')
    week = 1
    api_key = factory.Faker('text', max_nb_chars=64)


class ScheduleFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = models.Schedule
        abstract = False


class OrgUserFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = models.OrgUser
        abstract = False

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email_address = factory.Faker('email')
    active = True
    email_verified_on = datetime.utcnow()

    user = factory.SubFactory(
        UserFactory,
        username=factory.SelfAttribute('..email_address')
    )

    phone_number = factory.Faker('phone_number').generate()[0:20]
    phone_number_verified_on = datetime.utcnow()
    notification_type = 'email'
    role = 'admin'
    is_oncall = True
    code = factory.Faker('text', max_nb_chars=10)
    color = factory.Faker('color')


class IntervalScheduleFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = IntervalSchedule
        abstract = False


class PeriodicTaskFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = PeriodicTask
        abstract = False


class AlertFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = models.Alert
        abstract = False

    notification_type = 'team'
    incident_interval = 1
    doc_link = factory.Faker('url')
    active = True
    failure_count = 0


class PingFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = models.Ping
        abstract = False

    name = factory.Faker('text', max_nb_chars=30)
    active = True
    interval = 5
    status_code = 200
    expected_string = None
    expected_value = None
    endpoint = factory.Faker('url')
    endpoint_username = factory.Faker('first_name')
    endpoint_password = factory.Faker('password')
    content_type = 'text/plain'


class ResultFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = models.Result
        abstract = False


class FailureFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = models.Failure
        abstract = False


class BaseTest(TestCase):

    def setUp(self):

        random.seed(93074)

        mins = [5, 10, 15, 20, 25, 30]

        for m in mins:
            try:
                intsc = IntervalSchedule.objects.get(
                    every=m, period='minutes'
                )
            except IntervalSchedule.DoesNotExist:
                IntervalScheduleFactory.create(
                    every=m,
                    period='minutes'
                )
        try:
            intsc = IntervalSchedule.objects.get(
                every=1, period='days'
            )
        except IntervalSchedule.DoesNotExist:
            IntervalScheduleFactory.create(
                every=1,
                period='days'
            )

    def create_org_user(self, org, notification_type='email'):

        user = OrgUserFactory.create(
            org=org,
            notification_type=notification_type
        )
        schedule.add_user_to_schedule(user, org)

        return user

    def assertAlert(self, alert, org, payload):
        self.assertEqual(alert.org.id, org.id)
        self.assertEqual(
            alert.notification_type,
            payload['notification_type']
        )
        self.assertEqual(alert.doc_link, payload['doc_link'])
        self.assertEqual(alert.active, payload['active'])
        self.assertEqual(alert.failure_count, 0)
        self.assertEqual(alert.callback_url, payload['callback_url'])
        self.assertEqual(
            alert.callback_username,
            payload['callback_username']
        )
        self.assertEqual(
            alert.callback_password,
            payload['callback_password']
        )
        self.assertEqual(alert.notified_on, None)
