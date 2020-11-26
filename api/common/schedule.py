from api.models import Schedule


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
        pass


def change_user_order(start_index, end_index, org):

    sched = list(Schedule.objects.filter(org=org))

    current_user = sched.pop(start_index)
    sched.insert(end_index, current_user)

    for i, s in enumerate(sched):
        s.order = i + 1
        s.save()


def get_on_call_user(org):

    try:
        s = Schedule.objects.get(org=org, order=org.week)
        return s.org_user
    except Schedule.DoesNotExist:
        return None
