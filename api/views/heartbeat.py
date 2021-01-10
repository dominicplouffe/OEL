from rest_framework import filters
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule

from api.base import AuthenticatedViewSet
from api.models import Ping
from api.serializers import PingSerializer
from .pong import PongPermission


from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from tasks.heartbeat import process_heartbeat
from api.tools import cache
from oel.settings import SECS_BETWEEN_PONGS


class HeartBeatViewSet(AuthenticatedViewSet):
    serializer_class = PingSerializer
    filter_backends = [
        filters.SearchFilter,
        DjangoFilterBackend,
        filters.OrderingFilter
    ]
    permission_classes = [PongPermission]

    model = Ping
    filterset_fields = []
    ordering_fields = ['created_on', 'updated_on']

    def get_queryset(self, *args, **kwargs):

        if self.request.user.is_superuser:
            return super().get_queryset()

        return Ping.objects.filter(
            org=self.request.org,
            direction="push",
            heartbeat=True,
        ).all()

    def create(self, request, *args, **kwargs):

        ping_data = request.data
        ping_data['org'] = request.org.id
        ping_data['direction'] = 'push'
        ping_data['heartbeat'] = True

        # todo: fix the cron schedule input
        task_crontab = CrontabSchedule.objects.get_or_create(
            minute="*/5"  # ping_data['interval']
        )

        task = PeriodicTask(
            name=ping_data['name'],
            task='tasks.heartbeat.dead_man_switch',
            crontab=task_crontab,
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
        ping_data['direction'] = 'push'
        ping_data['heartbeat'] = True

        ping_serializer = PingSerializer(
            data=ping_data
        )

        if not ping_serializer.is_valid():
            return Response(
                ping_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        # todo: fix the cron schedule input
        ping = Ping.objects.get(id=ping_data['id'])
        task_crontab = CrontabSchedule.objects.get_or_create(
            minute="*/5"  # ping_data['interval']
        )

        ping.task.enabled = ping_data['active']
        ping.task.interval = task_crontab

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


@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def keep_alive(_, push_key):

    cache_key = 'xauth-req-%s' % push_key
    if cache.get(cache_key):
        return Response(
            {
                'details': 'Too many requests'
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )

    cache.set(cache_key, 1, expire=SECS_BETWEEN_PONGS)

    res = process_heartbeat(push_key)
    return Response({'heartbeat_received': res}, status=status.HTTP_200_OK)
