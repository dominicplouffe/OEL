from api.models import Metric
from datetime import datetime, timedelta


def get_graph_data(metric_name, tags, org, interval=60, since=1):

    interval = interval * 60

    now = datetime.utcnow()
    query_date = now - timedelta(hours=since)

    query = {
        'org': org,
        'created_on__gte': query_date
    }

    for k, v in tags.items():
        query['tags__%s' % k] = v

    mt = Metric.objects.filter(**query).order_by('-created_on')

    values = [
        {'created_on': m.created_on, 'value': m.metrics[metric_name]} for m in mt
    ]
    values.reverse()

    current_interval = values[0]['created_on']
    current_values = []

    graph_metrics = []

    for v in values:
        diff = v['created_on'] - current_interval
        if diff.total_seconds() >= interval:
            val = 0
            if len(current_values) > 0:
                val = sum(current_values) / len(current_values)
            graph_metrics.append({
                'date': v['created_on'],
                'value': val
            })

            current_interval = v['created_on']
            current_values = []

        current_values.append(v['value'])

    if len(current_values) > 0:
        graph_metrics.append({
            'date': v['created_on'],
            'value': sum(current_values) / len(current_values)
        })

    return graph_metrics
