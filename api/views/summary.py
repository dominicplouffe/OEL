from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from api.common import alert_summary
from rest_framework import status

from api import models
from api import serializers

objects = {
    'pong': {
        'model': models.Pong,
        'serializer': serializers.PongSerializer
    },
    'ping': {
        'model': models.Ping,
        'serializer': serializers.PingSerializer
    },
    'metric_condition': {
        'model': models.MetricCondition,
        'serializer': serializers.MetricConditionSerializer
    }
}


def convert(v):

    try:
        v = float(v)
        return v
    except ValueError:
        pass

    try:
        v = int(v)
        return v
    except ValueError:
        pass

    return v


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def summarizer(request, *args, **kwargs):

    org = request.org
    hours = int(request.GET.get('hours', 24))
    obj = objects[kwargs['object']]

    if 'id' in kwargs:
        objs = obj['model'].objects.filter(
            org=org,
            id=kwargs['id']
        )
    else:

        query = obj['model'].objects.filter(
            org=org
        )

        query_filter = request.GET.get('filter', None)
        objs = query.order_by('created_on')

        if query_filter and '=' in query_filter:
            filter_field = query_filter.split('=')[0]
            filter_value = convert(query_filter.split('=')[1])

            objs = [
                o for o in objs if getattr(o, filter_field) == filter_value
            ]

    summary = alert_summary.get_alert_summary(
        objs,
        obj['serializer'],
        hours=hours
    )

    return Response(
        summary,
        status=status.HTTP_200_OK
    )
