import json
import pytz
from api.models import Pong, Result
from rest_framework import filters
from api.base import AuthenticatedViewSet
from rest_framework.permissions import BasePermission, AllowAny
from rest_framework.permissions import AllowAny
from rest_framework.serializers import ModelSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from datetime import datetime, timedelta
from tasks.pong import process_pong
from api.models import Pong, Alert
from api.tools import cache
from oel.settings import SECS_BETWEEN_PONGS, PONG_DATA_MAX_LEN
from rest_framework.permissions import IsAuthenticated
from api.common import failure
from api.serializers import PongSerializer, FailureSerializer


class PongKeyPermission(BasePermission):
    def has_permission(self, request, view):

        xauth = request.headers.get('X-Auth', None)
        if xauth is None:
            return False

        try:
            pong = Pong.objects.get(push_key=xauth)
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

        return Response(
            PongSerializer(pong).data,
            status=status.HTTP_200_OK
        )


@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def pongme(request, push_key):

    cache_key = 'xauth-req-%s' % push_key
    if cache.get(cache_key):
        return Response(
            {
                'details': 'Too many requests'
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )

    cache.set(cache_key, 1, expire=SECS_BETWEEN_PONGS)

    res = process_pong(push_key)

    return Response({'notification_sent': res}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pong_summary(request, *args, **kwargs):

    org = request.org
    hours = int(request.GET.get('hours', 24))

    if 'id' in kwargs:
        pongs = Pong.objects.filter(
            org=org,
            id=kwargs['id']
        )
    else:
        pongs = Pong.objects.filter(
            org=org
        ).order_by('created_on')

    data = {
        'total': len(pongs),
        'active': 0,
        'paused': 0,
        'up': 0,
        'down': 0
    }
    pong_data = []

    now = datetime.now(pytz.UTC)
    now = datetime(now.year, now.month, now.day, now.hour)
    ago = now - timedelta(hours=hours)

    for pong in pongs:
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

        if pong.alert.failure_count > 0:
            data['down'] += 1
            pd['status'] = False
        else:
            data['up'] += 1

        if pong.active:
            data['active'] += 1
        else:
            data['paused'] += 1

        results = Result.objects.filter(
            alert=pong.alert,
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

            pd['stats'] = failure.get_fail_stats(pong.alert, hours)

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

        pd['pong'] = PongSerializer(pong).data
        if not pd['status']:
            fail = failure.get_current_failure(pong.alert)
            if fail:
                pd['fail'] = FailureSerializer(fail).data

        pong_data.append(pd)

    pong_data = sorted(pong_data, key=lambda x: -x['pong']['active'])
    return Response(
        {
            'totals': data,
            'pongs': pong_data
        },
        status=status.HTTP_200_OK
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
        status = 'success'
        status_text = 'Everything looks great today'

        if res.success / res.count < 0.90:
            status = 'danger'
            status_text = 'Many pongs failed on this day'
        elif res.failure > 1:
            status = 'warning'
            status_text = 'At least one failure on this day'

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
