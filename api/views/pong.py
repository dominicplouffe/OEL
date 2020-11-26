import json
from api.models import Ping, Result
from rest_framework import filters
from api.base import AuthenticatedViewSet
from rest_framework.permissions import BasePermission
from rest_framework.permissions import AllowAny
from rest_framework.serializers import ModelSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from datetime import datetime, timedelta
from tasks.pong import process_pong
from api.models import Ping
from api.tools import cache
from oel.settings import SECS_BETWEEN_PONGS, PONG_DATA_MAX_LEN


class PongKeyPermission(BasePermission):
    def has_permission(self, request, view):

        xauth = request.headers.get('X-Auth', None)
        if xauth is None:
            return False

        try:
            ping = Ping.objects.get(pong_key=xauth)
        except Ping.DoesNotExist:
            return False

        return True


@api_view(['POST'])
@permission_classes([PongKeyPermission])
def pongme(request, *args, **kwargs):

    xauth = request.headers['X-Auth']

    cache_key = 'xauth-req-%s' % xauth
    if cache.get(cache_key):
        return Response(
            {
                'details': 'Too many requests'
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )

    cache.set(cache_key, 1, expire=SECS_BETWEEN_PONGS)
    body = request.body.decode('utf-8', errors="ignore")

    if len(body) > PONG_DATA_MAX_LEN:
        return Response(
            {
                'details': 'Data too big.  Max length is: %s' % PONG_DATA_MAX_LEN
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    data = None
    if body:
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return Response(
                {
                    'details': 'Data must be valid JSON.  '
                    'Use https://jsonlint.com/ to validate your JSON.',
                    'data_received': body
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    res = process_pong(xauth, data)

    return Response({'notification_sent': res}, status=status.HTTP_200_OK)
