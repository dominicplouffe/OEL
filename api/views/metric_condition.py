from api.models import MetricCondition, VitalInstance, Alert
from rest_framework import filters
from rest_framework.permissions import BasePermission
from api.base import AuthenticatedViewSet
from django_filters.rest_framework import DjangoFilterBackend
from api.serializers import MetricConditionSerializer
from rest_framework import status
from rest_framework.response import Response


class MetricConditionPermission(BasePermission):

    def has_object_permission(self, request, view, object):
        if object.org.id == request.org.id:
            return True

        return False


class MetricConditionViewSet(AuthenticatedViewSet):
    serializer_class = MetricConditionSerializer
    filter_backends = [filters.SearchFilter,
                       DjangoFilterBackend, filters.OrderingFilter]
    permission_classes = [MetricConditionPermission]

    model = MetricCondition
    filterset_fields = ['instance_id']
    ordering_fields = ['created_on', 'updated_on']

    def create(self, request, *args, **kwargs):

        condition_data = request.data
        condition_data['org'] = request.org.id

        vital_instance = VitalInstance.objects.get(
            instance_id=condition_data['instance']
        )

        condition_data['instance'] = vital_instance.id

        condition_data_serializer = MetricConditionSerializer(
            data=condition_data
        )

        if not condition_data_serializer.is_valid():
            return Response(
                condition_data_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        condition_data_serializer.save()

        metric = MetricCondition.objects.get(
            id=condition_data_serializer.data['id']
        )
        alert = Alert(
            active=condition_data['active'],
            notification_type=condition_data['notification_type'],
            incident_interval=int(condition_data['incident_interval']),
            callback_url=condition_data['callback_url'],
            callback_username=condition_data['callback_username'],
            callback_password=condition_data['callback_password'],
            doc_link=condition_data['doc_link'],
            org=request.org
        )
        alert.save()

        metric.alert = alert
        metric.save()

        return Response(
            condition_data_serializer.data,
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        condition_data = request.data

        metric = MetricCondition.objects.get(
            id=kwargs['pk']
        )

        metric.alert.active = condition_data['active']
        metric.alert.notification_type = condition_data['notification_type']
        metric.alert.incident_interval = condition_data['incident_interval']
        metric.alert.callback_url = condition_data['callback_url']
        metric.alert.callback_username = condition_data['callback_username']
        metric.alert.callback_password = condition_data['callback_password']
        metric.alert.doc_link = condition_data['doc_link']
        metric.alert.save()

        metric.active = condition_data['active']
        metric.name = condition_data['name']
        metric.rule = condition_data['rule']
        metric.save()

        return Response(
            MetricConditionSerializer(metric).data,
            status=status.HTTP_200_OK
        )
