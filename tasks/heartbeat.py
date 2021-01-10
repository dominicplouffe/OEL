from api import models
from datetime import datetime


def process_heartbeat(push_key):
    pong = models.Ping.objects.filter(
        push_key=push_key,
        active=True,
        heartbeat=True
    ).first()

    if not pong:
        return False

    if not pong.active:
        return False

    pong.last_heartbeat = datetime.now()
    pong.save()

    return True
