from api.models import ScheduleOverride
from rest_framework import filters
from api.base import AuthenticatedViewSet
from rest_framework.permissions import BasePermission
from django_filters.rest_framework import DjangoFilterBackend, FilterSet

from api.serializers import ScheduleOverrideSerializer


class ScheduleOverridePermission(BasePermission):

    def has_object_permission(self, request, view, object):
        if object.org.id == request.org.id:
            return True

        return False


class OrderFilterSet(FilterSet):

    class Meta:
        model = ScheduleOverride

        fields = {
            'start_date': ['lt', 'gt', 'lte', 'gte', 'exact'],
            'end_date': ['lt', 'gt', 'lte', 'gte', 'exact']
        }


class ScheduleOverrideViewSet(AuthenticatedViewSet):
    serializer_class = ScheduleOverrideSerializer
    filter_backends = [filters.SearchFilter,
                       DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = OrderFilterSet
    permission_classes = [ScheduleOverridePermission]

    model = ScheduleOverride
    ordering_fields = ['start_date', 'end_date']
