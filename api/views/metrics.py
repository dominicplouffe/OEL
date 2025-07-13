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

    payload = json.loads(request.body.decode("utf-8"))
    api_key = payload.get("api-key", None)

    if not api_key:
        return Response(
            {"error": '"api_key" key needs to be in URL'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        org = Org.objects.get(api_key=api_key)
    except Org.DoesNotExist:
        return Response(
            {"error": "vital metric is innactive"}, status=status.HTTP_400_BAD_REQUEST
        )

    if "metric" not in payload:
        return Response(
            {"error": '"metric" key needs to be in payload'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(payload["metric"]) == 0:
        return Response(
            {"error": '"metric" needs to contain one or more values'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if "value" not in payload:
        return Response(
            {"error": '"value" key needs to be in metric payload'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if (
        payload["value"] is None
        or payload["value"] == ""
        or not isinstance(payload["value"], (int, float))
    ):
        return Response(
            {"error": '"value" must be a number'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if payload["value"] != 0:
        m = Metric(
            org=org, metric_name=payload["metric"], metric_value=payload["value"]
        )
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
    Get all metrics for a given metric.
    """

    all_metrics = (
        Metric.objects.filter(org=request.org)
        .distinct("metric_name")
        .values_list("metric_name", flat=True)
    )

    return Response({"metrics": all_metrics}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_metric_values(request, tag_name):
    """
    Get the values for a given metric and tags.
    """

    def get_deltas(period):
        query_delta = {
            "1h": timedelta(hours=1),
            "3h": timedelta(hours=3),
            "12h": timedelta(hours=12),
            "24h": timedelta(days=1),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30),
        }
        res_delta = {
            "1h": timedelta(minutes=1),
            "3h": timedelta(minutes=5),
            "12h": timedelta(minutes=30),
            "24h": timedelta(hours=1),
            "7d": timedelta(hours=12),
            "30d": timedelta(days=1),
        }

        formatter = {
            "1h": "%Y-%m-%d %H:%M",
            "3h": "%Y-%m-%d %H:%M",
            "12h": "%Y-%m-%d %H:%M",
            "24h": "%Y-%m-%d %H:%M",
            "7d": "%Y-%m-%d",
            "30d": "%Y-%m-%d",
        }

        return query_delta, res_delta, formatter

    def round_datetime(created_on, period, formatter):
        # based on format, we need to group by the period
        if period == "1h":  # round to the nearest minute
            p = created_on.strftime(formatter[period])
        elif period == "3h":  # round to the nearest 5 minutes
            # round p.created_on to the nearest 5 minutes
            p = created_on - timedelta(
                minutes=created_on.minute % 5,
                seconds=created_on.second,
                microseconds=created_on.microsecond,
            )
            p = p.strftime(formatter[period])
        elif period == "12h":  # round to the nearest 30 minutes
            # round p.created_on to the nearest 30 minutes
            p = created_on - timedelta(
                minutes=created_on.minute % 30,
                seconds=created_on.second,
                microseconds=created_on.microsecond,
            )
            p = p.strftime(formatter[period])
        elif period == "24h":  # round to the nearest hour
            p = created_on.replace(minute=0, second=0, microsecond=0)
            p = p.strftime(formatter[period])
        elif period == "7d":  # round to the nearest day
            p = created_on.replace(hour=0, minute=0, second=0, microsecond=0)
            p = p.strftime(formatter[period])
        else:  # round to the nearest day
            p = created_on.replace(hour=0, minute=0, second=0, microsecond=0)

        return p

    try:
        period = request.GET.get("period", "24h")
        if period not in ["1h", "3h", "12h", "24h", "7d", "30d"]:
            return Response(
                {"error": 'Invalid period. Use "1h", "3h", "12h", "24h", "7d", "30d"'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        delta, res_delta, formatter = get_deltas(period)
        since = datetime.now(tz=timezone.utc) - delta[period]

        metrics = Metric.objects.filter(
            org=request.org, metric_name=tag_name, created_on__gte=since
        )

        print(since, period)

        values = {}
        total = 0
        for m in metrics:

            p = round_datetime(m.created_on, period, formatter)

            total += m.metric_value
            if p not in values:
                values[p] = {"total": 0}
            values[p]["total"] += m.metric_value

        dt = datetime.now(tz=timezone.utc) - delta[period]
        end = datetime.now(tz=timezone.utc)
        result = {
            "period": period,
            "total": total,
            "since": dt.strftime("%Y-%m-%d %H:%M:%S"),
            "values": [],
        }
        while dt <= end:
            p = round_datetime(dt, period, formatter)
            if p not in values:
                values[p] = {"total": 0}
            result["values"].append({"time": p, "value": values[p]["total"]})
            dt += res_delta[period]

        return Response(
            result,
            status=status.HTTP_200_OK,
        )
    except Metric.DoesNotExist:
        return Response(
            values,
            status=status.HTTP_200_OK,
        )
