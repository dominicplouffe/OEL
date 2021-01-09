from api.models import PingHeader
from rest_framework import filters
from api.base import AuthenticatedViewSet
from rest_framework.permissions import BasePermission
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import ModelSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from datetime import datetime, timedelta
from collections import defaultdict

from api.serializers import PingHeaderSerializer


class PingHeaderPermission(BasePermission):

    def has_object_permission(self, request, view, object):

        return request.org.id == object.alert.org.id


class PingHeaderViewSet(AuthenticatedViewSet):
    serializer_class = PingHeaderSerializer
    filter_backends = [filters.SearchFilter,
                       DjangoFilterBackend, filters.OrderingFilter]
    permission_classes = [PingHeaderPermission]

    model = PingHeader
    filterset_fields = ['alert', 'header_type']
    ordering_fields = []
