from api.models import Metric
from datetime import datetime, timedelta

rule = {
    'category': 'memory_percent',
    'metric': 'mem',
    'metric_rollup': 'value',  # value, sum, avg
    'timespan': {
        'value': 7,
        'span': 'days',  # days, hours
    },
    'op': '>',  # <, <=, ==, >=, >,
    'value': 0.2
}


def check_notification_rule(org, instance_id, rule, send_notification=False):

    value = get_value(org, instance_id, rule)

    trigger = False
    if rule['op'] == '<':
        if value < rule['value']:
            trigger = True
    elif rule['op'] == '<=':
        if value <= rule['value']:
            trigger = True
    elif rule['op'] == '==':
        if value == rule['value']:
            trigger = True
    elif rule['op'] == '>=':
        if value >= rule['value']:
            trigger = True
    if rule['op'] == '>':
        if value > rule['value']:
            trigger = True

    print(value, trigger)

    if trigger and send_notification:
        # Send the notification
        pass


def get_value(org, instance_id, rule):
    value = None

    if rule['metric_rollup'] == 'value':

        value = Metric.objects.filter(
            org=org,
            tags__identifier=instance_id,
            tags__category=rule['category']
        ).order_by('-created_on')[0].metrics[rule['metric']]

    elif rule['metric_rollup'] == 'sum':

        if rule['timespan']['span'] == 'hours':
            created_on = datetime.utcnow() - timedelta(
                hours=rule['timespan']['value']
            )
        else:
            created_on = datetime.utcnow() - timedelta(
                days=rule['timespan']['value']
            )

        stats = Metric.objects.filter(
            org=org,
            tags__identifier=instance_id,
            tags__category=rule['category'],
            created_on__gte=created_on
        ).order_by('-created_on')

        value = sum([
            s.metrics[rule['metric']] for s in stats
        ])

    elif rule['metric_rollup'] == 'avg':

        if rule['timespan']['span'] == 'hours':
            created_on = datetime.utcnow() - timedelta(
                hours=rule['timespan']['value']
            )
        else:
            created_on = datetime.utcnow() - timedelta(
                days=rule['timespan']['value']
            )

        stats = Metric.objects.filter(
            org=org,
            tags__identifier=instance_id,
            tags__category=rule['category'],
            created_on__gte=created_on
        ).order_by('-created_on')

        vals = [s.metrics[rule['metric']] for s in stats]
        value = sum(vals) / len(vals)

    else:
        raise ValueError('Invalid metric_rollup')

    return value
