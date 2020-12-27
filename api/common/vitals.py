from api.models import VitalInstance


def is_vitals_payload(payload):

    if 'identifier' not in payload['tags']:
        return False

    return True


def process_incoming_vitals(payload, org):

    if not is_vitals_payload(payload):
        return

    instance_id = payload['tags']['identifier']

    try:
        instance = VitalInstance.objects.get(instance_id=instance_id)
    except VitalInstance.DoesNotExist:
        instance = VitalInstance(
            instance_id=instance_id,
            name=instance_id,
            org=org,
            active=True
        )
        instance.save()

    if not instance.active:
        return

    return True
