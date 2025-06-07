from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from api.common import vitals
from api.common.metrics import notification

from datetime import datetime, timedelta, timezone

from api.models import Org, Metric
import json


@api_view(["POST"])
@permission_classes([AllowAny])
def add_metrics(request, *args, **kwargs):

    try:
        org = Org.objects.get(api_key=kwargs["api_key"])
    except Org.DoesNotExist:
        return Response(
            {"error": "vital metric is innactive"}, status=status.HTTP_400_BAD_REQUEST
        )

    payload = json.loads(request.body.decode("utf-8"))

    proceed = True
    if vitals.is_vitals_payload(payload):
        if not vitals.process_incoming_vitals(payload, org):
            proceed = False

    if not proceed:
        return Response({}, status=status.HTTP_201_CREATED)

    if "metrics" not in payload:
        return Response(
            {"error": '"metrics" key needs to be in payload'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(payload["metrics"]) == 0:
        return Response(
            {"error": '"metrics" needs to contain one or more values'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if "tags" not in payload:
        return Response(
            {"error": '"tags" key needs to be in payload'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(payload["tags"]) == 0:
        return Response(
            {"error": '"tags" needs to contain one or more values'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if "partition" in payload["tags"]:
        if payload["tags"]["partition"] != "/":
            return Response({}, status=status.HTTP_201_CREATED)

    if "cpu" in payload["metrics"]:
        payload["metrics"]["cpu"] = payload["metrics"]["cpu"] / 100

    m = Metric(org=org, metrics=payload["metrics"], tags=payload["tags"])
    m.save()

    return Response({}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def metric_sample(request, *args, **kwargs):

    payload = json.loads(request.body.decode("utf-8"))

    value = notification.get_value(request.org, payload["instance_id"], payload["rule"])

    return Response({"value": value}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_metrics_tags(request, *args, **kwargs):
    """
    Get all tags for a given metric.
    """

    all_tags = Metric.objects.filter(org=request.org).values_list("tags", flat=True)
    unique_tags = set()
    for tags_list in all_tags:
        if isinstance(tags_list, list):
            unique_tags.update(tags_list)
        elif isinstance(tags_list, dict):
            unique_tags.update(tags_list.keys())
    tags = list(unique_tags)

    return Response({"tags": tags}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_metric_values(request, tag_name):
    """
    Get the values for a given metric and tags.
    """
    try:
        period = request.GET.get("period", "24h")
        if period not in ["1h", "3h", "12h", "24h", "7d", "30d"]:
            return Response(
                {"error": 'Invalid period. Use "1h", "3h", "12h", "24h", "7d", "30d"'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        since = (
            datetime.now(tz=timezone.utc)
            - {
                "1h": timedelta(hours=1),
                "3h": timedelta(hours=3),
                "12h": timedelta(hours=12),
                "24h": timedelta(days=1),
                "7d": timedelta(days=7),
                "30d": timedelta(days=30),
            }[period]
        )

        metrics = Metric.objects.filter(
            org=request.org, tags__contains=tag_name, created_on__gte=since
        )

        values = {}
        for m in metrics:
            for key, value in m.metrics.items():
                if key not in values:
                    values[key] = {"total": 0, "period": {}}

                if period in ["1h", "3h", "12h", "24h"]:
                    p = m.created_on.strftime("%Y-%m-%d %H:00")
                else:
                    p = m.created_on.strftime("%Y-%m-%d")

                if p not in values[key]["period"]:
                    values[key]["period"][p] = 0

                values[key]["period"][p] += value
                values[key]["total"] += value

                for _, v in values.items():
                    st = since
                    now = datetime.now(tz=timezone.utc)
                    while st <= now:
                        if period in ["1h", "3h", "12h", "24h"]:
                            dt = st.strftime("%Y-%m-%d %H:00")
                        else:
                            dt = st.strftime("%Y-%m-%d")
                        v["period"][dt] = v["period"].get(dt, 0)

                        if period in ["1h", "3h", "12h", "24h"]:
                            st += timedelta(hours=1)
                        else:
                            st += timedelta(days=1)
        return Response(
            values,
            status=status.HTTP_200_OK,
        )
    except Metric.DoesNotExist:
        return Response(
            values,
            status=status.HTTP_200_OK,
        )
