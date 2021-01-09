import json
from api.models import Metric
from api.common import schedule
from tasks.ping import insert_failure
from datetime import datetime, timedelta
from api.common.result import process_result

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


def check_notification_rule(
    condition,
    send_notification=False
):

    org = condition.org
    instance_id = condition.instance.instance_id
    rule = condition.rule

    print(rule)

    value = get_value(org, instance_id, rule)

    trigger = False
    if rule['op'] == '<':
        if value < float(rule['value']):
            trigger = True
    elif rule['op'] == '<=':
        if value <= float(rule['value']):
            trigger = True
    elif rule['op'] == '==':
        if value == float(rule['value']):
            trigger = True
    elif rule['op'] == '>=':
        if value >= float(rule['value']):
            trigger = True
    if rule['op'] == '>':
        if value > float(rule['value']):
            trigger = True

    if trigger and send_notification:
        oncall_user = schedule.get_on_call_user(condition.org)

        fail_res = insert_failure(
            condition.alert,
            'Metric triggered',
            500,
            "",
            oncall_user
        )

        return process_result(
            False,
            condition.alert,
            fail_res,
            '%s.%s' % (rule['category'], rule['metric']),
            oncall_user
        )

    return False


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
                hours=int(rule['timespan']['value'])
            )
        else:
            created_on = datetime.utcnow() - timedelta(
                days=int(rule['timespan']['value'])
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
                hours=int(rule['timespan']['value'])
            )
        else:
            created_on = datetime.utcnow() - timedelta(
                days=int(rule['timespan']['value'])
            )

        stats = Metric.objects.filter(
            org=org,
            tags__identifier=instance_id,
            tags__category=rule['category'],
            created_on__gte=created_on
        ).order_by('-created_on')

        vals = [s.metrics[rule['metric']] for s in stats]
        value = 0
        if len(vals) > 0:
            value = sum(vals) / len(vals)
        print(value)
    else:
        raise ValueError('Invalid metric_rollup')

    return value
