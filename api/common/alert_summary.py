import pytz
from api.models import Result
from api.common import failure
from datetime import datetime, timedelta
from api.serializers import FailureSerializer


def get_alert_summary(objects, serializer, hours=24):

    data = {
        'total': len(objects),
        'active': 0,
        'paused': 0,
        'up': 0,
        'down': 0
    }
    object_data = []

    now = datetime.now(pytz.UTC)
    now = datetime(now.year, now.month, now.day, now.hour)
    ago = now - timedelta(hours=hours)

    for object in objects:
        pd = {
            'status': True,
            'count': 0,
            'success': 0,
            'failure': 0,
            'total_time': 0,
            'avg_resp': 0.00,
            'downtime': 0,
            'downtime_s': '0m 0s',
            'availability': 0.000,
            'snapshot': {}
        }

        start = ago + timedelta(hours=1)
        while start <= now:
            pd['snapshot'][start] = {
                'success': 0,
                'failure': 0,
                'count': 0,
                'status': None,
                'avg_res': 0,
                'date': start
            }
            start += timedelta(hours=1)

        if object.alert.failure_count > 0:
            data['down'] += 1
            pd['status'] = False
        else:
            data['up'] += 1

        if object.active:
            data['active'] += 1
        else:
            data['paused'] += 1

        results = Result.objects.filter(
            alert=object.alert,
            result_type='hour',
            result_date__gte=ago
        ).order_by('result_date')

        pd['downtime'] = 0
        pd['avg_resp'] = 0
        pd['total_time'] = 0
        pd['availability'] = 0

        for res in results:
            pd['count'] += res.count
            pd['success'] += res.success
            pd['failure'] += res.failure

            if hasattr(object, 'interval'):
                pd['downtime'] += object.interval * res.failure * 60
                pd['total_time'] += res.total_time
                pd['avg_resp'] = pd['total_time'] / pd['count']
                pd['availability'] = round(
                    100*pd['success'] / pd['count'],
                    2
                )

            pd['stats'] = failure.get_fail_stats(object.alert, hours)

            downtime_hours = int(pd['downtime'] / 60 / 60)
            downtime_minutes = int((
                pd['downtime'] - (downtime_hours * 60 * 60)
            ) / 60)

            pd['downtime_s'] = '%sh %sm' % (downtime_hours, downtime_minutes)

            res_date = res.result_date
            res_date = datetime(
                res_date.year, res_date.month, res_date.day, res_date.hour
            )

            if res_date in pd['snapshot']:
                pd['snapshot'][res_date] = {
                    'success': res.success,
                    'failure': res.failure,
                    'count': res.count,
                    'status': None,
                    'avg_res': res.total_time / res.count,
                    'date': res_date
                }
                if res.count == res.success:
                    pd['snapshot'][res_date]['status'] = 'success'
                elif res.count == res.failure:
                    pd['snapshot'][res_date]['status'] = 'danger'
                else:
                    pd['snapshot'][res_date]['status'] = 'warning'

        pd['snapshot'] = [
            y for x, y in sorted(pd['snapshot'].items(), key=lambda x: x[0])
        ]

        pd['object'] = serializer(object).data
        if not pd['status']:
            fail = failure.get_current_failure(object.alert)
            if fail:
                pd['fail'] = FailureSerializer(fail).data

        object_data.append(pd)

    object_data = sorted(object_data, key=lambda x: -x['object']['active'])

    return {
        'objects': object_data,
        'totals': data
    }
