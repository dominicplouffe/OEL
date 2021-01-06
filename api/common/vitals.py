from api.models import VitalInstance, Metric
from datetime import datetime, timedelta


def is_vitals_payload(payload):

    if 'identifier' not in payload['tags']:
        return False

    return True


def process_incoming_vitals(payload, org):

    if not is_vitals_payload(payload):
        return

    instance_id = payload['tags']['identifier']

    try:
        instance = VitalInstance.objects.get(instance_id=instance_id)
    except VitalInstance.DoesNotExist:
        instance = VitalInstance(
            instance_id=instance_id,
            name=instance_id,
            org=org,
            active=True
        )
        instance.save()

    if not instance.active:
        return

    return True


def get_cpu_stats(instance_id, org, since=1):

    now = datetime.utcnow()
    query_date = now - timedelta(hours=since)

    stats = Metric.objects.filter(
        org=org,
        tags__identifier=instance_id,
        tags__category='cpu_percent',
        created_on__gte=query_date
    ).order_by('-created_on')

    percents = []
    for s in stats:
        percents.append(
            s.metrics['cpu']
        )

    if len(percents) == 0:
        return 0.00

    return sum(percents) / len(percents)


def get_mem_stats(instance_id, org, since=1):

    now = datetime.utcnow()
    query_date = now - timedelta(hours=since)

    stats = Metric.objects.filter(
        org=org,
        tags__identifier=instance_id,
        tags__category='memory_percent',
        created_on__gte=query_date
    ).order_by('-created_on')

    percents = []
    for s in stats:
        percents.append(
            s.metrics['mem']
        )

    if len(percents) == 0:
        return 0.00

    return sum(percents) / len(percents)


def get_disk_stats(instance_id, org, partition='/', since=1):

    now = datetime.utcnow()
    query_date = now - timedelta(hours=since)

    stats = Metric.objects.filter(
        org=org,
        tags__identifier=instance_id,
        tags__category='disk_percent',
        tags__partition=partition,
        created_on__gte=query_date
    ).order_by('-created_on')

    percents = []
    for s in stats:
        percents.append(
            s.metrics['disk']
        )

    if len(percents) == 0:
        return 0.00

    return sum(percents) / len(percents)
