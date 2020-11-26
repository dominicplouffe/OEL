from django.utils.functional import SimpleLazyObject
from api.models import OrgUser, Org


def get_org(request):
    if not request.user.id:
        return None
    org_user = OrgUser.objects.filter(user=request.user, active=True).first()
    return org_user.org


def get_org_user(request):
    if not request.user.id:
        return None
    org_user = OrgUser.objects.filter(user=request.user, active=True).first()
    return org_user


def org_middleware(get_response):

    def middleware(request):

        request.org = SimpleLazyObject(lambda: get_org(request))
        request.org_user = SimpleLazyObject(lambda: get_org_user(request))

        response = get_response(request)
        return response
    return middleware
