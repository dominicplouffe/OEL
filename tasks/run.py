from celery import shared_task


@shared_task
def run_task(*args, **kwargs):
    """
    A generic task runner that can be used to execute any task by name.
    """
    print("aaaaaa")
