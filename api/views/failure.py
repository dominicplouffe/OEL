from api.models import Failure, Ping
from rest_framework import filters
from api.base import AuthenticatedViewSet
from api.views.org_user import OrgUserSerializer
from rest_framework.permissions import BasePermission
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import ModelSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from tasks.ping import process_ping
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from datetime import datetime, timedelta
from collections import defaultdict

from api.serializers import FailureSerializer


class FailurePermission(BasePermission):

    def has_object_permission(self, request, view, object):
        if request.user.is_superuser:
            return True

        return False


class FailureViewSet(AuthenticatedViewSet):
    serializer_class = FailureSerializer
    filter_backends = [filters.SearchFilter,
                       DjangoFilterBackend, filters.OrderingFilter]
    permission_classes = [FailurePermission]

    model = Failure
    filterset_fields = ['ping']
    ordering_fields = ['created_on', 'status_code']


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def failure_count(request, ping_id):
    org = request.org

    try:
        ping = Ping.objects.get(org=org, pk=ping_id)
    except Ping.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    failures = Failure.objects.filter(ping=ping)

    counts = defaultdict(int)
    reasons = {x: y for x, y in Failure.REASON}
    total = 0

    for f in failures:
        if f.reason and f.reason in reasons:
            counts[reasons[f.reason]] += 1
            total += 1

    results = []
    for r, c in counts.items():
        results.append({
            'reason': r,
            'percentage': c / total,
            'count': c
        })

    return Response(results, status=status.HTTP_200_OK)
