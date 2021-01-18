from api import models
from datetime import datetime
from tasks.notification import notification_check


def process_result(
    success,
    alert,
    fail_res,
    name,
    obj_name,
    obj_id,
    oncall_user,
    diff=0
):
    now = datetime.utcnow()
    hour_date = datetime(
        now.year, now.month, now.day,
        now.hour, 0, 0
    )
    day_date = datetime(
        now.year, now.month, now.day
    )

    # Increment Result Hour
    result_hour = models.Result.objects.filter(
        alert=alert,
        result_type='hour',
        result_date=hour_date
    ).first()

    if result_hour is None:
        result_hour = models.Result(
            alert=alert,
            result_type='hour',
            result_date=hour_date,
            count=0,
            success=0,
            failure=0,
            total_time=0
        )

    result_hour.count += 1
    if success:
        result_hour.success += 1
    else:
        result_hour.failure += 1

    result_hour.total_time += diff
    result_hour.save()

    # Increment Result Day
    result_day = models.Result.objects.filter(
        alert=alert,
        result_type='day',
        result_date=day_date
    ).first()

    if result_day is None:
        result_day = models.Result(
            alert=alert,
            result_type='day',
            result_date=day_date,
            count=0,
            success=0,
            failure=0,
            total_time=0
        )

    result_day.count += 1
    if success:
        result_day.success += 1
    else:
        result_day.failure += 1

    result_day.total_time += diff
    result_day.save()

    return notification_check(
        success,
        alert,
        result_day,
        fail_res,
        diff,
        oncall_user,
        name,
        obj_name,
        obj_id,
    )
