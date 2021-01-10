from api import models
from api.common import schedule
from tasks.ping import insert_failure
from api.common.result import process_result


def process_pong(push_key):

    pong = models.Pong.objects.filter(
        push_key=push_key,
        active=True
    ).first()

    if not pong:
        return False

    if not pong.active:
        return False

    oncall_user = schedule.get_on_call_user(pong.org)

    fail_res = insert_failure(
        pong.alert,
        "receive_alert",
        500,
        "",
        oncall_user
    )

    return process_result(
        False,
        pong.alert,
        fail_res,
        pong.name,
        oncall_user
    )
