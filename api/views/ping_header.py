from api.models import PingHeader
from rest_framework import filters
from api.base import AuthenticatedViewSet
from rest_framework.permissions import BasePermission
from django_filters.rest_framework import DjangoFilterBackend

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
