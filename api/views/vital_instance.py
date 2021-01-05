from api.models import VitalInstance
from rest_framework import filters
from rest_framework.permissions import BasePermission
from api.base import AuthenticatedViewSet
from django_filters.rest_framework import DjangoFilterBackend
from api.serializers import VitalInstanceSerializer
from rest_framework import status
from rest_framework.response import Response
from api.common import vitals
from api.common.metrics import graph
from tools.color import get_gradient


class VitalInstancePermission(BasePermission):

    def has_object_permission(self, request, view, object):
        if object.org.id == request.org.id:
            return True

        return False


class VitalInstancegViewSet(AuthenticatedViewSet):
    serializer_class = VitalInstanceSerializer
    filter_backends = [filters.SearchFilter,
                       DjangoFilterBackend, filters.OrderingFilter]
    permission_classes = [VitalInstancePermission]

    model = VitalInstance
    filterset_fields = ['name', 'instance_id']
    ordering_fields = ['created_on', 'updated_on']

    def retrieve(self, request, pk=None):
        try:
            instance = VitalInstance.objects.get(pk=pk)

            instance = self.get_instance_details(
                VitalInstanceSerializer(instance).data,
                request.org
            )

            cpu_graph = graph.get_graph_data(
                'cpu',
                {
                    'category': 'cpu_percent',
                    'identifier': instance['instance_id']
                },
                request.org,
                since=24
            )
            mem_graph = graph.get_graph_data(
                'mem',
                {
                    'category': 'memory_percent',
                    'identifier': instance['instance_id']
                },
                request.org,
                since=24
            )
            disk_graph = graph.get_graph_data(
                'disk',
                {
                    'category': 'disk_percent',
                    'partition': '/',
                    'identifier': instance['instance_id']
                },
                request.org,
                since=24
            )

            instance['cpu_graph'] = cpu_graph
            instance['mem_graph'] = mem_graph
            instance['disk_graph'] = disk_graph

            return Response(
                instance,
                status=status.HTTP_200_OK
            )
        except VitalInstance.DoesNotExist:
            return Response(
                {'error': 'instance not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def list(self, request, *args, **kwargs):

        response = super().list(request, *args, **kwargs)

        for i, instance in enumerate(response.data['results']):

            response.data['results'][i] = self.get_instance_details(
                response.data['results'][i],
                request.org
            )

        return response

    def get_queryset(self, *args, **kwargs):

        instances = VitalInstance.objects.filter(org=self.request.org).all()

        return instances

    def get_instance_details(self, instance, org):
        instance['cpu_percent'] = vitals.get_cpu_stats(
            instance['instance_id'],
            org
        )
        instance['cpu_status'] = get_gradient(int(
            instance['cpu_percent'] * 100)
        )
        instance['mem_percent'] = vitals.get_mem_stats(
            instance['instance_id'],
            org
        )
        instance['mem_status'] = get_gradient(int(
            instance['mem_percent'] * 100)
        )

        instance['disk_percent'] = vitals.get_disk_stats(
            instance['instance_id'],
            org
        )
        instance['disk_status'] = get_gradient(int(
            instance['disk_percent'] * 100)
        )

        total = (instance['cpu_percent'] +
                 instance['mem_percent'] +
                 instance['disk_percent']
                 ) / 3

        instance['total_status'] = get_gradient(int(total * 100))

        return instance
