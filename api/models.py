from datetime import datetime

from django.db import models
from django.contrib.auth.models import User
from django_celery_beat.models import PeriodicTask, IntervalSchedule

# Create your models here.


class Org(models.Model):

    name = models.CharField(max_length=200, null=False)
    week = models.IntegerField(null=False, blank=False, default=1)
    api_key = models.CharField(max_length=64, null=False, blank=False)
    created_on = models.DateTimeField(default=datetime.now)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class OrgUser(models.Model):
    NOTIFICATION_TYPE = (
        ('email', 'Email'),
        ('text', 'Text')
    )
    ROLES = (
        ('admin', 'Admin'),
        ('user', 'User')
    )

    first_name = models.CharField(max_length=50, null=False, blank=False)
    last_name = models.CharField(max_length=50, null=False, blank=False)
    email_address = models.CharField(max_length=50, null=False, blank=False)
    active = models.BooleanField(default=False)
    email_verified_on = models.DateTimeField(null=True, blank=True)
    org = models.ForeignKey(Org, on_delete=models.CASCADE, null=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        blank=True,
        default=None,
        null=True
    )
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    phone_number_verified_on = models.DateTimeField(null=True, blank=True)
    notification_type = models.CharField(
        max_length=20,
        null=False,
        blank=False,
        choices=NOTIFICATION_TYPE,
        default="email"
    )
    role = models.CharField(
        max_length=20,
        null=False,
        blank=False,
        choices=ROLES,
        default="admin"
    )
    is_oncall = models.BooleanField(default=False)
    code = models.CharField(null=True, blank=True, max_length=10)
    color = models.CharField(max_length=10, null=True, blank=True)
    created_on = models.DateTimeField(default=datetime.now)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{0} {1} ({2})'.format(
            self.first_name,
            self.last_name,
            self.org.name
        )


class Ping(models.Model):
    CONTENT_TYPE = (
        ('text/plain', 'Text'),
        ('application/json', 'JSON')
    )

    NOTIFICATION_TYPE = (
        ('team', 'Team'),
        ('callback', 'Callback')
    )

    DIRECTION = (
        ('push', 'Push'),
        ('pull', 'Pull')
    )

    org = models.ForeignKey(Org, on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=30, null=False, blank=False)
    doc_link = models.CharField(max_length=255, null=True, blank=True)
    direction = models.CharField(
        max_length=10,
        default='pull',
        choices=DIRECTION
    )
    heartbeat = models.BooleanField(
        default=False
    )
    notification_type = models.CharField(
        max_length=20,
        null=False,
        blank=False,
        choices=NOTIFICATION_TYPE
    )

    incident_interval = models.IntegerField(null=False, blank=False, default=1)

    active = models.BooleanField(default=True)
    failure_count = models.IntegerField(default=0)

    # How to communicate the failures
    callback_url = models.CharField(max_length=255, null=True, blank=True)
    callback_userame = models.CharField(max_length=255, null=True, blank=True)
    callback_password = models.CharField(max_length=255, null=True, blank=True)

    notified_on = models.DateTimeField(null=True, blank=True)
    created_on = models.DateTimeField(default=datetime.now)
    updated_on = models.DateTimeField(auto_now=True)

    # Ping Settings
    endpoint = models.CharField(max_length=255, null=True, blank=True)
    endpoint_username = models.CharField(max_length=255, null=True, blank=True)
    endpoint_password = models.CharField(max_length=255, null=True, blank=True)
    interval = models.IntegerField(null=True, blank=True)
    period = models.CharField(
        max_length=24,
        choices=IntervalSchedule.PERIOD_CHOICES,
        default='minutes'
    )
    task = models.ForeignKey(
        PeriodicTask,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    # Expected Results for Ping
    status_code = models.IntegerField(null=True, blank=True)
    content_type = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=CONTENT_TYPE
    )
    expected_string = models.CharField(max_length=1000, null=True, blank=True)
    expected_value = models.CharField(max_length=1000, null=True, blank=True)

    # Pong and Heartbeat Settings
    push_key = models.CharField(max_length=255, null=True, blank=True)

    # Heartbeat Settings
    last_heartbeat = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return '{0}({1})'.format(
            self.org.name,
            self.name
        )


class PingHeader(models.Model):
    HEADER_TYPE = (
        ('endpoint', 'Endpoint'),
        ('callback', 'Callback')
    )
    ping = models.ForeignKey(
        Ping,
        on_delete=models.CASCADE,
        null=False
    )
    key = models.CharField(max_length=255, null=False, blank=False)
    value = models.CharField(max_length=255, null=False, blank=False)
    header_type = models.CharField(
        max_length=20,
        null=False,
        blank=False,
        choices=HEADER_TYPE
    )
    created_on = models.DateTimeField(default=datetime.now)
    updated_on = models.DateTimeField(auto_now=True)


class Result(models.Model):
    RESULT_TYPE = (
        ('hour', 'Hour'),
        ('day', 'Day')
    )
    ping = models.ForeignKey(
        Ping,
        on_delete=models.CASCADE,
        null=False
    )
    result_date = models.DateTimeField(null=False, blank=False)
    result_type = models.CharField(
        max_length=20,
        null=False,
        blank=False,
        choices=RESULT_TYPE
    )
    count = models.IntegerField(null=False)
    success = models.IntegerField(null=False)
    failure = models.IntegerField(null=False)
    total_time = models.FloatField(null=False)
    created_on = models.DateTimeField(default=datetime.now)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{0} - {1} - {2} - {3}'.format(
            self.ping.org.name,
            self.ping.name,
            self.result_type,
            self.result_date.strftime('%Y-%m-%d %H:00')
        )


class Failure(models.Model):
    REASON = (
        ('invalid_value', 'Invalid Value'),
        ('key_error', 'Key Error'),
        ('value_error', 'Value Error'),
        ('status_code', 'Status Code'),
        ('connection_error', 'Connection Error'),
        ('timeout_error', 'Timeout Error'),
        ('http_error', 'HTTP Error'),
        ('receive_alert', 'Receive Alert')
    )
    ping = models.ForeignKey(
        Ping,
        on_delete=models.CASCADE,
        null=False
    )
    status_code = models.IntegerField(null=False)
    reason = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=REASON
    )
    notify_org_user = models.ForeignKey(
        OrgUser,
        on_delete=models.CASCADE,
        null=True
    )
    content = models.CharField(
        max_length=10000, null=True, blank=True)
    created_on = models.DateTimeField(default=datetime.now)
    acknowledged_on = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(
        OrgUser,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='acknowledged_by'
    )
    fixed_on = models.DateTimeField(null=True, blank=True)
    fixed_by = models.ForeignKey(
        OrgUser,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='fixed_by'
    )
    ignored_on = models.DateTimeField(null=True, blank=True)
    ignored_by = models.ForeignKey(
        OrgUser,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='ignored_by'
    )
    recovered_on = models.DateTimeField(null=True, blank=True)


class PongData(models.Model):

    pong = models.ForeignKey(Ping, on_delete=models.CASCADE, null=False)
    created_on = models.DateTimeField(default=datetime.now)
    data = models.JSONField(null=False, blank=False)


class Schedule(models.Model):
    org = models.ForeignKey(Org, on_delete=models.CASCADE, null=True)
    org_user = models.ForeignKey(OrgUser, on_delete=models.CASCADE, null=False)
    order = models.IntegerField(null=False)

    def __str__(self):
        return '{0} - {1} - {2}'.format(
            self.org.name,
            self.org_user.email_address,
            self.order,
        )


class NotificationBody(models.Model):

    TYPES = (
        ('recovery', 'Recovery'),
        ('failure', 'Failure'),
        ('going-oncall', 'Going OnCall'),
        ('invite', 'Invitation'),
        ('confirmation', 'Confirmation'),
    )
    DELIVERY_METHOD = (
        ('email', 'Email'),
        ('text', 'Text')
    )

    org = models.ForeignKey(Org, on_delete=models.CASCADE, null=True)
    notification_type = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=TYPES
    )
    content = models.CharField(max_length=10000, null=True, blank=True)
    delivery = models.CharField(
        max_length=20, null=True, blank=True, choices=DELIVERY_METHOD
    )


class Metric(models.Model):
    org = models.ForeignKey(Org, on_delete=models.CASCADE, null=True)
    metrics = models.JSONField()
    tags = models.JSONField()
    created_on = models.DateTimeField(default=datetime.now)


class VitalInstance(models.Model):
    org = models.ForeignKey(Org, on_delete=models.CASCADE, null=True)
    instance_id = models.CharField(max_length=256, null=True, blank=True)
    name = models.CharField(max_length=256, null=True, blank=True)
    active = models.BooleanField(default=True)
    created_on = models.DateTimeField(default=datetime.now)
    updated_on = models.DateTimeField(auto_now=True)
