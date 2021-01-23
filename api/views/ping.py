from api.models import Ping, Result, Failure, Alert
from rest_framework import filters
from api.base import AuthenticatedViewSet
from rest_framework.permissions import BasePermission
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from tasks.ping import process_ping, insert_failure, do_ping
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from datetime import datetime, timedelta

from api.serializers import PingSerializer


class PingPermission(BasePermission):

    def has_object_permission(self, request, view, object):
        if request.user.is_superuser:
            return True

        if object.org.id == request.org.id:
            return True

        return False


class PingViewSet(AuthenticatedViewSet):
    serializer_class = PingSerializer
    filter_backends = [filters.SearchFilter,
                       DjangoFilterBackend, filters.OrderingFilter]
    permission_classes = [PingPermission]

    model = Ping
    filterset_fields = []
    ordering_fields = ['created_on', 'updated_on']

    def destroy(self, request, *args, **kwargs):

        ping = Ping.objects.get(pk=kwargs['pk'])
        ping.alert.delete()
        ping.delete()

        # TODO Delete Results and Failures

        return Response(
            {},
            status=status.HTTP_200_OK
        )

    def get_queryset(self, *args, **kwargs):

        return Ping.objects.filter(org=self.request.org).all()

    def create(self, request, *args, **kwargs):

        ping_data = request.data
        ping_data['org'] = request.org.id

        task_interval = IntervalSchedule.objects.get(
            every=ping_data['interval'],
            period="minutes"
        )
        task = PeriodicTask(
            name='Ping: %s' % ping_data['name'],
            task='tasks.ping.process_ping',
            interval=task_interval
        )
        task.save()
        ping_data['task'] = task.id

        ping_serializer = PingSerializer(
            data=ping_data
        )

        if not ping_serializer.is_valid():
            return Response(
                ping_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        ping_serializer.save()

        ping = Ping.objects.get(id=ping_serializer.data['id'])
        alert = Alert(
            active=ping_data['active'],
            notification_type=ping_data['notification_type'],
            incident_interval=int(ping_data['incident_interval']),
            callback_url=ping_data['callback_url'],
            callback_username=ping_data['callback_username'],
            callback_password=ping_data['callback_password'],
            doc_link=ping_data['doc_link'],
            org=request.org
        )
        alert.save()

        ping.alert = alert
        ping.save()

        task.args = [ping_serializer.data['id']]
        task.save()

        return Response(
            ping_serializer.data,
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        ping_data = request.data

        ping_data['org'] = request.org.id

        ping_serializer = PingSerializer(
            data=ping_data
        )

        if not ping_serializer.is_valid():
            return Response(
                ping_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        ping = Ping.objects.get(id=ping_data['id'])
        task_interval = IntervalSchedule.objects.get(
            every=ping_data['interval']
        )
        task_interval.enabled = ping_data['active']
        ping.task.interval = task_interval

        ping.alert.active = ping_data['active']
        ping.alert.notification_type = ping_data['notification_type']
        ping.alert.incident_interval = int(ping_data['incident_interval'])
        ping.alert.callback_url = ping_data['callback_url']
        ping.alert.callback_username = ping_data['callback_username']
        ping.alert.callback_password = ping_data['callback_password']
        ping.alert.doc_link = ping_data['doc_link']
        ping.alert.save()

        for attr, value in ping_data.items():
            if attr == 'org':
                continue
            setattr(ping, attr, value)
        ping.save()
        ping.task.save()

        return Response(
            PingSerializer(ping).data,
            status=status.HTTP_200_OK
        )


class PingTestRequestSerializer(serializers.Serializer):
    endpoint = serializers.URLField(max_length=2048)
    expected_str = serializers.CharField(
        max_length=255, required=True, allow_blank=True)
    expected_value = serializers.CharField(
        max_length=255, required=False, allow_blank=True)
    content_type = serializers.CharField(max_length=255, required=True)
    status_code = serializers.IntegerField(required=True)
    username = serializers.CharField(
        max_length=255, required=False, allow_blank=True)
    password = serializers.CharField(
        max_length=255, required=False, allow_blank=True)
    headers = serializers.DictField(required=False, default=dict)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ping_test2(request):

    ping_req = PingTestRequestSerializer(data=request.data)
    ping_req.is_valid(raise_exception=True)

    res = {
        'http_status_code': 0,
        'content': "",
        'check_status': False,
        'reason': None
    }
    auth = None
    if ping_req.validated_data[
        'username'
    ] and ping_req.validated_data['password']:
        auth = (
            ping_req.validated_data['username'],
            ping_req.validated_data['password'],
        )
    headers = {}
    if ping_req.validated_data['headers']:
        headers = ping_req.validated_data['headers']

    ping_res, reason, _, _ = do_ping(
        ping_req.validated_data['endpoint'],
        ping_req.validated_data['expected_str'],
        ping_req.validated_data['expected_value'],
        ping_req.validated_data['content_type'],
        ping_req.validated_data['status_code'],
        auth=auth,
        headers=headers
    )

    if ping_res:
        res['http_status_code'] = ping_res.status_code
        res['content'] = ping_res.content.decode('utf-8')
    res['check_status'] = reason is None
    res['reason'] = reason

    return Response(res)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ping_details(request, id):
    ping = Ping.objects.get(pk=id)

    if not ping:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if ping.org.id != request.org.id:
        return Response(
            status=status.HTTP_403_FORBIDDEN
        )

    now = datetime.utcnow()
    now = datetime(now.year, now.month, now.day)
    ago = now - timedelta(days=359)

    calendar = {
        'start': ago.strftime('%Y-%m-%d'),
        'end': now.strftime('%Y-%m-%d'),
        'data': []
    }
    d = ago

    calendar_data = {}
    while d <= now:
        calendar_data[d] = {
            'date': d.strftime('%Y-%m-%d'),
            'status': None,
            'text': None
        }
        d += timedelta(days=1)

    results = Result.objects.filter(
        alert=ping.alert,
        result_type='day',
        result_date__gte=ago
    ).order_by('result_date')

    for res in results:
        d = res.result_date
        d = datetime(d.year, d.month, d.day)
        status_msg = 'success'
        status_text = 'Everything looks great today'

        if res.success / res.count < 0.90:
            status_msg = 'danger'
            status_text = 'Many pings failed on this day'
        elif res.failure > 1:
            status_msg = 'warning'
            status_text = 'At least one failure on this day'

        calendar_data[d]['status'] = status_msg
        calendar_data[d]['text'] = status_text
        calendar_data[d]['success'] = res.success
        calendar_data[d]['failure'] = res.failure
        calendar_data[d]['count'] = res.count
        calendar_data[d]['success_rate'] = res.success / res.count

    calendar['data'] = [
        y for x, y in sorted(calendar_data.items(), key=lambda x: x[0])
    ]

    return Response({
        'calendar': calendar
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ping_now(request, id):
    res = process_ping(
        id, failure=insert_failure
    )

    if res is None:
        ping_res = 'OK'
        reason = 'n/a'
    else:
        ping_res = res[0]
        reason = res[1]

    return Response(
        {
            'ping_reason': ping_res,
            'reason': reason
        },
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def acknowledge(request, id):

    try:
        fail = Failure.objects.get(pk=id)
    except Failure.DoesNotExist:
        return Response(
            {},
            status=status.HTTP_404_NOT_FOUND
        )

    fail.acknowledged_on = datetime.utcnow()
    fail.acknowledged_by = request.org_user
    fail.save()

    return Response(
        {},
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fix(request, id):

    try:
        fail = Failure.objects.get(pk=id)
    except Failure.DoesNotExist:
        return Response(
            {},
            status=status.HTTP_404_NOT_FOUND
        )

    fail.fixed_on = datetime.utcnow()
    fail.fixed_by = request.org_user

    fail.alert.failure_count = 0
    fail.save()
    fail.alert.save()

    return Response(
        {},
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ignore(request, id):

    try:
        fail = Failure.objects.get(pk=id)
    except Failure.DoesNotExist:
        return Response(
            {},
            status=status.HTTP_404_NOT_FOUND
        )

    fail.ignored_on = datetime.utcnow()
    fail.ignored_by = request.org_user

    fail.alert.failure_count = 0
    fail.save()
    fail.alert.save()

    return Response(
        {},
        status=status.HTTP_200_OK
    )
