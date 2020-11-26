from api import models
from datetime import datetime
from tasks.notification import notification_check


def process_pong(pong_key, data):

    return False
    # pong = models.PingPong.objects.filter(
    #     pong_key=pong_key,
    #     active=True
    # ).first()

    # if not pong:
    #     return False

    # if not pong.active:
    #     return False

    # now = datetime.utcnow()
    # hour_date = datetime(
    #     now.year, now.month, now.day,
    #     now.hour, 0, 0
    # )
    # day_date = datetime(
    #     now.year, now.month, now.day
    # )

    # # Increment Result Hour
    # result_hour = models.Result.objects.filter(
    #     pingpong=pong,
    #     result_type='hour',
    #     result_date=hour_date
    # ).first()

    # if result_hour is None:
    #     result_hour = models.Result(
    #         pingpong=pong,
    #         result_type='hour',
    #         result_date=hour_date,
    #         count=0,
    #         success=0,
    #         failure=0,
    #         total_time=0
    #     )

    # result_hour.count += 1
    # result_hour.failure += 1
    # result_hour.save()

    # # Increment Result Day
    # result_day = models.Result.objects.filter(
    #     ping=pong,
    #     result_type='day',
    #     result_date=day_date
    # ).first()

    # if result_day is None:
    #     result_day = models.Result(
    #         ping=pong,
    #         result_type='day',
    #         result_date=day_date,
    #         count=0,
    #         success=0,
    #         failure=0,
    #         total_time=0
    #     )

    # result_day.count += 1
    # result_day.failure += 1
    # result_day.save()

    # if data:
    #     pong_data = models.PongData(
    #         data=data,
    #         pong=pong
    #     )
    #     pong_data.save()

    # success = False
    # return notification_check(success, pong, result_day, 'Pong Received', 0)
