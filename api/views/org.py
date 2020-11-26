from api.models import Org
from rest_framework import filters
from api.base import AuthenticatedViewSet
from rest_framework.permissions import BasePermission
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes

from api.serializers import OrgSerializer


class OrgPermission(BasePermission):

    def has_object_permission(self, request, view, object):
        if request.user.is_superuser:
            return True

        return False


class OrgViewSet(AuthenticatedViewSet):
    serializer_class = OrgSerializer
    filter_backends = [filters.SearchFilter,
                       DjangoFilterBackend, filters.OrderingFilter]
    permission_classes = [OrgPermission]

    model = Org
    filterset_fields = []
    ordering_fields = ['created_on']
