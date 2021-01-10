import pytz
from api.models import Ping, Result, Failure
from rest_framework import filters
from api.base import AuthenticatedViewSet
from api.common import failure
from rest_framework.permissions import BasePermission
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from tasks.ping import process_ping, insert_failure
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from datetime import datetime, timedelta

from api.serializers import PingSerializer, FailureSerializer


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
    filterset_fields = ['direction']
    ordering_fields = ['created_on', 'updated_on']

    def get_queryset(self, *args, **kwargs):

        return Ping.objects.filter(org=self.request.org).all()

    def create(self, request, *args, **kwargs):

        ping_data = request.data
        ping_data['org'] = request.org.id

        task_interval, _ = IntervalSchedule.objects.get_or_create(
            every=ping_data['interval'],
            period=IntervalSchedule.MINUTES  # todo: pull from period data when front end starts passing default
        )
        task = PeriodicTask(
            name=ping_data['name'],
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
        task_interval, _ = IntervalSchedule.objects.get_or_create(
            every=ping_data['interval'],
            period=IntervalSchedule.MINUTES  # todo: pull from period data when front end starts passing default
        )
        task_interval.enabled = ping_data['active']
        ping.task.interval = task_interval

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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ping_summary(request, *args, **kwargs):

    org = request.org
    direction = request.GET.get('direction', 'pull')
    heartbeat = request.GET.get('heartbeat', False)
    hours = int(request.GET.get('hours', 24))

    if 'id' in kwargs:
        pings = Ping.objects.filter(
            org=org,
            id=kwargs['id'],
            direction=direction,
            heartbeat=heartbeat
        )
    else:
        pings = Ping.objects.filter(
            org=org,
            direction=direction,
            heartbeat=heartbeat
        ).order_by('created_on')

    data = {
        'total': len(pings),
        'active': 0,
        'paused': 0,
        'up': 0,
        'down': 0
    }
    ping_data = []

    now = datetime.now(pytz.UTC)
    now = datetime(now.year, now.month, now.day, now.hour)
    ago = now - timedelta(hours=hours)

    for ping in pings:
        pd = {
            'status': True,
            'count': 0,
            'success': 0,
            'failure': 0,
            'total_time': 0,
            'avg_resp': 0.00,
            'downtime': 0,
            'downtime_s': '0m 0s',
            'availability': 0.000,
            'snapshot': {}
        }

        start = ago + timedelta(hours=1)
        while start <= now:
            pd['snapshot'][start] = {
                'success': 0,
                'failure': 0,
                'count': 0,
                'status': None,
                'avg_res': 0,
                'date': start
            }
            start += timedelta(hours=1)

        if ping.failure_count > 0:
            data['down'] += 1
            pd['status'] = False
        else:
            data['up'] += 1

        if ping.active:
            data['active'] += 1
        else:
            data['paused'] += 1

        results = Result.objects.filter(
            ping=ping,
            result_type='hour',
            result_date__gte=ago
        ).order_by('result_date')

        pd['downtime'] = 0
        pd['avg_resp'] = 0
        pd['total_time'] = 0
        pd['availability'] = 0

        for res in results:
            pd['count'] += res.count
            pd['success'] += res.success
            pd['failure'] += res.failure

            if ping.direction == 'pull':
                pd['downtime'] += ping.interval * res.failure * 60
                pd['total_time'] += res.total_time
                pd['avg_resp'] = pd['total_time'] / pd['count']
                pd['availability'] = round(
                    100*pd['success'] / pd['count'],
                    2
                )

            pd['stats'] = failure.get_fail_stats(ping, hours)

            downtime_hours = int(pd['downtime'] / 60 / 60)
            downtime_minutes = int((
                pd['downtime'] - (downtime_hours * 60 * 60)
            ) / 60)

            pd['downtime_s'] = '%sh %sm' % (downtime_hours, downtime_minutes)

            res_date = res.result_date
            res_date = datetime(
                res_date.year, res_date.month, res_date.day, res_date.hour
            )

            if res_date in pd['snapshot']:
                pd['snapshot'][res_date] = {
                    'success': res.success,
                    'failure': res.failure,
                    'count': res.count,
                    'status': None,
                    'avg_res': res.total_time / res.count,
                    'date': res_date
                }
                if res.count == res.success:
                    pd['snapshot'][res_date]['status'] = 'success'
                elif res.count == res.failure:
                    pd['snapshot'][res_date]['status'] = 'danger'
                else:
                    pd['snapshot'][res_date]['status'] = 'warning'

        pd['snapshot'] = [
            y for x, y in sorted(pd['snapshot'].items(), key=lambda x: x[0])
        ]

        pd['ping'] = PingSerializer(ping).data
        if not pd['status']:
            fail = failure.get_current_failure(ping)
            if fail:
                pd['fail'] = FailureSerializer(fail).data

        ping_data.append(pd)

    ping_data = sorted(ping_data, key=lambda x: -x['ping']['active'])
    return Response(
        {
            'totals': data,
            'pings': ping_data
        },
        status=status.HTTP_200_OK
    )


@ api_view(['GET'])
@ permission_classes([IsAuthenticated])
def ping_test(request, id):

    def insert_failure_tmp(ping, reason, status_code, content, org_user):
        pass

    ping = Ping.objects.get(pk=id)

    if not ping:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if ping.org.id != request.org.id:
        return Response(status=status.HTTP_403_FORBIDDEN)

    res = {
        'http_status_code': 0,
        'content': "",
        'check_status': False,
        'reason': None
    }

    ping_res, reason = process_ping(
        ping.id, failure=insert_failure_tmp, process_res=False
    )

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
        return Response(status=status.HTTP_403_FORBIDDEN)

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
        ping=ping,
        result_type='day',
        result_date__gte=ago
    ).order_by('result_date')

    for res in results:
        d = res.result_date
        d = datetime(d.year, d.month, d.day)
        status = 'success'
        status_text = 'Everything looks great today'

        if ping.direction == 'pull':
            if res.success / res.count < 0.90:
                status = 'danger'
                status_text = 'Many pings failed on this day'
            elif res.failure > 1:
                status = 'warning'
                status_text = 'At least one failure on this day'
        else:
            if res.count >= 5:
                status = 'danger'
                status_text = 'Many pongs were triggered on this day'
            elif res.count >= 1:
                status = 'warning'
                status_text = 'One or more pongs where triggered on this day'

        calendar_data[d]['status'] = status
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
        id, failure=insert_failure, process_res=True
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

    fail.ping.failure_count = 0
    fail.save()
    fail.ping.save()

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

    fail.ping.failure_count = 0
    fail.save()
    fail.ping.save()

    return Response(
        {},
        status=status.HTTP_200_OK
    )
