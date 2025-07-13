def setup_oel():
    from django_celery_beat.models import PeriodicTask, CrontabSchedule

    # Create or get the crontab schedule for midnight
    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute="0",
        hour="0",
        day_of_week="*",
        day_of_month="*",
        month_of_year="*",
        timezone="UTC",  # Change this if needed
    )

    # Create or get the periodic task
    task, created = PeriodicTask.objects.get_or_create(
        name="Reschedule Pings",
        defaults={
            "crontab": schedule,
            "task": "tasks.schedule.reschedule",
        },
    )

    # If task already exists but doesn't have the correct schedule/task, update it
    if not created:
        task.crontab = schedule
        task.task = "tasks.schedule.reschedule"
        task.save()
