from datetime import datetime
from api.models import Schedule, OrgUser, ScheduleOverride


def add_user_to_schedule(org_user, org):

    users = Schedule.objects.filter(org=org).order_by('order')

    if len(users) == 0:
        s = Schedule(
            org_user=org_user,
            org=org,
            order=1
        )
        s.save()

    else:
        s = Schedule(
            org_user=org_user,
            org=org,
            order=list(users)[-1].order + 1
        )
        s.save()


def remove_user_from_schedule(org_user, org):

    try:
        usr = Schedule.objects.get(org_user=org_user, org=org)

        # TODO We should be able to do that with an update query
        users = Schedule.objects.filter(org=org, order__gt=usr.order)

        for u in users:
            if u.org_user.id == org_user.id:
                continue
            u.order -= 1
            u.save()

        usr.delete()
    except Schedule.DoesNotExist:
        return None


def update_user_order(user_id, org, new_index):
    try:
        usr = OrgUser.objects.get(id=user_id, org=org)

        sched = Schedule.objects.get(org=org, org_user=usr)
        sched.order = new_index
        sched.save()

    except OrgUser.DoesNotExist:
        return None


def get_on_call_user(org, current_date=None):

    if current_date is None:
        current_date = datetime.utcnow()

    try:
        over = ScheduleOverride.objects.get(
            start_date__gte=current_date, end_date__lte=current_date
        )

        return over.org_user
    except ScheduleOverride.DoesNotExist:
        pass

    try:
        s = Schedule.objects.get(org=org, order=org.week)
        return s.org_user
    except Schedule.DoesNotExist:
        return None
