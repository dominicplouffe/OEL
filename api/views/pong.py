from datetime import datetime, timedelta

from api.base import AuthenticatedViewSet
from api.models import Alert, Pong, Result, PongTrigger
from api.serializers import PongSerializer
from api.tools import cache
from django_filters.rest_framework import DjangoFilterBackend
from oel.settings import SECS_BETWEEN_PONGS
from rest_framework import filters, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import (AllowAny, BasePermission,
                                        IsAuthenticated)
from rest_framework.response import Response
from tasks.pong import process_pong
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from croniter import CroniterBadCronError, croniter


class PongKeyPermission(BasePermission):
    def has_permission(self, request, view):

        xauth = request.headers.get('X-Auth', None)
        if xauth is None:
            return False

        try:
            Pong.objects.get(push_key=xauth)
        except Pong.DoesNotExist:
            return False

        return True


class PongPermission(BasePermission):

    def has_object_permission(self, request, view, object):
        if request.user.is_superuser:
            return True

        if object.org.id == request.org.id:
            return True

        return False


class PongViewSet(AuthenticatedViewSet):
    serializer_class = PongSerializer
    filter_backends = [filters.SearchFilter,
                       DjangoFilterBackend, filters.OrderingFilter]
    permission_classes = [PongPermission]

    model = Pong
    filterset_fields = []
    ordering_fields = ['created_on', 'updated_on']

    def destroy(self, request, *args, **kwargs):

        pong = Pong.objects.get(pk=kwargs['pk'])
        pong.alert.delete()
        pong.delete()

        # TODO Delete Results and Failures

        return Response(
            {},
            status=status.HTTP_200_OK
        )

    def create(self, request, *args, **kwargs):

        pong_data = request.data
        pong_data['org'] = request.org.id

        task_interval = IntervalSchedule.objects.get(
            every=5
        )
        task = PeriodicTask(
            name=pong_data['name'],
            task='tasks.pong.process_pong_alert',
            interval=task_interval
        )
        task.save()
        pong_data['task'] = task.id

        pong_serializer = PongSerializer(
            data=pong_data
        )

        if not pong_serializer.is_valid():
            return Response(
                pong_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        pong_serializer.save()

        pong = Pong.objects.get(id=pong_serializer.data['id'])
        alert = Alert(
            active=pong_data['active'],
            notification_type=pong_data['notification_type'],
            incident_interval=int(pong_data['incident_interval']),
            callback_url=pong_data['callback_url'],
            callback_username=pong_data['callback_username'],
            callback_password=pong_data['callback_password'],
            doc_link=pong_data['doc_link'],
            org=request.org
        )
        alert.save()

        pong.alert = alert
        pong.save()

        task.args = [pong_serializer.data['id']]
        task.save()

        for t in pong_data['triggers']:
            newt = PongTrigger(
                trigger_type=t['trigger_type'],
                interval_value=int(t['interval']),
                unit=t['unit'],
                pong=pong
            )
            newt.save()

        return Response(
            pong_serializer.data,
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        pong_data = request.data
        pong_data['org'] = request.org.id

        pong_serializer = PongSerializer(
            data=pong_data
        )

        if not pong_serializer.is_valid():
            return Response(
                pong_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        pong = Pong.objects.get(id=pong_data['id'])

        pong.alert.active = pong_data['active']
        pong.alert.notification_type = pong_data['notification_type']
        pong.alert.incident_interval = int(pong_data['incident_interval'])
        pong.alert.callback_url = pong_data['callback_url']
        pong.alert.callback_username = pong_data['callback_username']
        pong.alert.callback_password = pong_data['callback_password']
        pong.alert.doc_link = pong_data['doc_link']
        pong.alert.save()

        for attr, value in pong_data.items():
            if attr == 'org':
                continue
            setattr(pong, attr, value)
        pong.save()

        for t in pong_data['triggers']:
            if t['id']:
                newt = PongTrigger.objects.get(id=t['id'])
                if not t['is_delete']:
                    newt.trigger_type = t['trigger_type']
                    newt.interval_value = t['interval_value']
                    newt.unit = t['unit']
                    newt.save()
                else:
                    newt.delete()
            if not t['id']:
                newt = PongTrigger(
                    trigger_type=t['trigger_type'],
                    interval_value=int(t['interval']),
                    unit=t['unit'],
                    pong=pong
                )
                newt.save()

        return Response(
            PongSerializer(pong).data,
            status=status.HTTP_200_OK
        )


@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def pongme(request, pos, push_key):

    cache_key = 'xauth-req-%s-%s' % (push_key, pos)
    if cache.get(cache_key):
        return Response(
            {
                'details': 'Too many requests'
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )

    cache.set(cache_key, 1, expire=SECS_BETWEEN_PONGS)

    res = process_pong(pos, push_key)

    return Response({'notification_sent': res}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_cron(request):

    cron = request.data.get('cron', '')

    try:
        ex = croniter.expand(cron)[0]

        return Response(
            {'data': ex},
            status=status.HTTP_200_OK
        )

    except CroniterBadCronError:

        return Response(
            {'error': 'Invalid Cron'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pong_details(request, id):
    pong = Pong.objects.get(pk=id)

    if not pong:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if pong.org.id != request.org.id:
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
        alert=pong.alert,
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
            status_text = 'Many pongs failed on this day'
        elif res.failure > 1:
            status_msg = 'warning'
            status_text = 'At least one failure on this day'

        if res.count >= 5:
            status_msg = 'danger'
            status_text = 'Many pongs were triggered on this day'
        elif res.count >= 1:
            status_msg = 'warning'
            status_text = 'One or more pongs were triggered on this day'

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
