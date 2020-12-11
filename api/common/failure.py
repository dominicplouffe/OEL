from api import models
from django.db.models import Q
from datetime import datetime, timedelta


def get_current_failure(ping):

    try:
        fail = models.Failure.objects.get(
            Q(ping=ping) &
            # Q(acknowledged_on__isnull=True) &
            Q(fixed_on__isnull=True) &
            Q(ignored_on__isnull=True) &
            Q(recovered_on__isnull=True)
        )

        return fail

    except models.Failure.DoesNotExist:
        return None


def recover_failure(ping):

    fail = get_current_failure(ping)

    if fail:
        fail.recovered_on = datetime.utcnow()
        fail.save()


def get_fail_stats(ping, hours):

    now = datetime.utcnow()
    ago = now - timedelta(hours=hours)

    fails = models.Failure.objects.filter(created_on__gte=ago, ping=ping)

    stats = {
        'total_time': 0.00,
        'total_fails': 0,
        'acknowledged': 0,
        'fixed': 0,
        'ignored': 0,
        'resolved': 0
    }
    for f in fails:
        created_on = f.created_on

        if f.recovered_on is not None:
            stats['total_time'] += (
                f.recovered_on - f.created_on
            ).total_seconds()
            stats['total_fails'] += 1
            stats['resolved'] += 1
        elif f.fixed_on is not None:
            stats['total_time'] += (f.fixed_on - f.created_on).total_seconds()
            stats['total_fails'] += 1
        elif f.ignored_on is not None:
            stats['total_time'] += (f.ignored_on -
                                    f.created_on).total_seconds()
            stats['total_fails'] += 1

        if f.fixed_on is not None:
            stats['fixed'] += 1
        if f.ignored_on is not None:
            stats['ignored'] += 1
        if f.acknowledged_on is not None:
            stats['acknowledged'] += 1

    fail_hours = int(stats['total_time'] / 60 / 60)
    fail_minutes = int((
        stats['total_time'] - (fail_hours * 60 * 60)
    ) / 60)

    stats['total_time_s'] = '%sh %sm' % (fail_hours, fail_minutes)

    return stats
