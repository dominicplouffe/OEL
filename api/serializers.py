from rest_framework.serializers import (
    ModelSerializer, ReadOnlyField, SerializerMethodField, BooleanField
)
from api.models import (
    Org, OrgUser, Failure, PingHeader, Ping, Schedule, VitalInstance, Alert,
    Pong, MetricCondition, PongTrigger
)
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password


class OrgSerializer(ModelSerializer):

    class Meta:
        model = Org
        fields = '__all__'


class AlertSerializer(ModelSerializer):

    class Meta:
        model = Alert
        fields = '__all__'


class PingSerializer(ModelSerializer):

    alert = AlertSerializer(read_only=True)

    class Meta:
        model = Ping
        fields = '__all__'


class PongTriggerSerializer(ModelSerializer):

    interval_error = BooleanField(default=False)
    is_delete = BooleanField(default=False)

    class Meta:
        model = PongTrigger
        fields = '__all__'


class PongSerializer(ModelSerializer):

    alert = AlertSerializer(read_only=True)
    triggers = SerializerMethodField()

    class Meta:
        model = Pong
        fields = '__all__'

    def get_triggers(self, pong):

        triggers = []

        for t in PongTrigger.objects.filter(pong=pong):
            triggers.append(PongTriggerSerializer(t).data)

        return triggers


class VitalInstanceSerializer(ModelSerializer):

    cpu_percent = ReadOnlyField()
    cpu_status = ReadOnlyField()
    mem_percent = ReadOnlyField()
    mem_status = ReadOnlyField()
    disk_percent = ReadOnlyField()
    disk_status = ReadOnlyField()
    total_status = ReadOnlyField()

    class Meta:
        model = VitalInstance
        fields = '__all__'


class OrgUserSerializer(ModelSerializer):

    org = OrgSerializer(read_only=True)
    schedule = SerializerMethodField()

    class Meta:
        model = OrgUser
        fields = '__all__'

    def get_schedule(self, org_user):

        try:
            usr = Schedule.objects.get(org_user=org_user, org=org_user.org)

            return ScheduleSerializer(usr).data
        except Schedule.DoesNotExist:
            return None


class FailureSerializer(ModelSerializer):

    notify_org_user = OrgUserSerializer(read_only=True)
    ping = PingSerializer(read_only=True)
    acknowledged_by = OrgUserSerializer(read_only=True)
    fixed_by = OrgUserSerializer(read_only=True)
    ignored_by = OrgUserSerializer(read_only=True)

    class Meta:
        model = Failure
        fields = '__all__'


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        exclude = ['password']


class PingHeaderSerializer(ModelSerializer):

    class Meta:
        model = PingHeader
        fields = '__all__'


class ChangePasswordSerializer(ModelSerializer):

    class Meta:
        model = User
        fields = ['password']

    # TODO huh?
    def _validate_password(self, password):
        user = self.context.get('user')
        validate_password(password, user)
        return password


class ScheduleSerializer(ModelSerializer):

    class Meta:
        model = Schedule
        fields = '__all__'


class MetricConditionSerializer(ModelSerializer):

    alert = AlertSerializer(read_only=True)

    class Meta:
        model = MetricCondition
        fields = '__all__'
