from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from api.models import Org, Metric
import json


@api_view(['POST'])
@permission_classes([AllowAny])
def add_metrics(request, *args, **kwargs):

    try:
        org = Org.objects.get(api_key=kwargs['api_key'])
    except Org.DoesNotExist:
        return Response(
            {},
            status=status.HTTP_404_NOT_FOUND
        )

    payload = json.loads(request.body.decode('utf-8'))

    if 'metrics' not in payload:
        return Response(
            {'error': '"metrics" key needs to be in payload'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(payload['metrics']) == 0:
        return Response(
            {'error': '"metrics" needs to contain one or more values'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if 'tags' not in payload:
        return Response(
            {'error': '"tags" key needs to be in payload'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(payload['tags']) == 0:
        return Response(
            {'error': '"tags" needs to contain one or more values'},
            status=status.HTTP_400_BAD_REQUEST
        )

    m = Metric(
        org=org,
        metrics=payload['metrics'],
        tags=payload['tags']
    )
    m.save()

    return Response(
        {},
        status=status.HTTP_201_CREATED
    )
