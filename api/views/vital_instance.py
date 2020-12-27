from api.models import VitalInstance
from rest_framework import filters
from rest_framework.permissions import BasePermission
from api.base import AuthenticatedViewSet
from django_filters.rest_framework import DjangoFilterBackend
from api.serializers import VitalInstanceSerializer
from rest_framework import status
from rest_framework.response import Response
from api.common import vitals
from tools.color import GRADIENTS


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

            instance.cpu_percent = vitals.get_cpu_stats(
                instance.instance_id,
                request.org
            )
            instance.cpu_status = GRADIENTS[int(instance.cpu_percent * 100)]
            instance.mem_percent = vitals.get_mem_stats(
                instance.instance_id,
                request.org
            )
            instance.mem_status = GRADIENTS[int(instance.mem_percent * 100)]

            instance.disk_percent = vitals.get_disk_stats(
                instance.instance_id,
                request.org
            )
            instance.disk_status = GRADIENTS[int(instance.disk_percent * 100)]

            total = (instance.cpu_percent +
                     instance.mem_percent +
                     instance.disk_percent
                     ) / 3

            instance.total_status = GRADIENTS[int(total * 100)]

            return Response(
                VitalInstanceSerializer(instance).data,
                status=status.HTTP_200_OK
            )
        except VitalInstance.DoesNotExist:
            return Response(
                {'error': 'instance not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def get_queryset(self, *args, **kwargs):

        return VitalInstance.objects.filter(org=self.request.org).all()
