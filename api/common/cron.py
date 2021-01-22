from datetime import datetime
from croniter import CroniterBadCronError, croniter


def is_now_ok(cron_desc):

    try:
        ex = croniter.expand(cron_desc)[0]

        now = datetime.utcnow()

        chour = ex[1]
        cdaymonth = ex[2]
        cmonth = ex[3]
        cdayweek = ex[4]

        nhour = now.hour
        ndaymonth = now.day
        nmonth = now.month
        ndayweek = now.weekday() + 1

        if chour[0] != '*':
            if nhour not in chour:
                return False

        if cdaymonth[0] != '*':
            if ndaymonth not in cdaymonth:
                return False

        if cmonth[0] != '*':
            if nmonth not in cmonth:
                return False

        if cdayweek[0] != '*':
            if ndayweek not in cdayweek:
                return False

    except CroniterBadCronError:
        return False

    return True
