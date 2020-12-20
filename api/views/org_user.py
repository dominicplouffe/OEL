import re
import json
from random import randrange
from api.models import OrgUser, Org, Schedule
from django.contrib.auth.models import User
from api.base import AuthenticatedViewSet
from rest_framework.permissions import BasePermission
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.serializers import ModelSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from api.common import schedule
from rest_framework.response import Response
from django.http.request import QueryDict
from datetime import datetime
from api.tools import mail, cache, colors
from api.views.org import OrgSerializer

from api.serializers import OrgUserSerializer


class OrgUserPermission(BasePermission):

    def has_object_permission(self, request, view, object):
        if request.user.is_superuser:
            return True

        return False


class OrgUserViewSet(AuthenticatedViewSet):

    serializer_class = OrgUserSerializer
    permission_classes = [OrgUserPermission]
    filter_backends = [
        filters.SearchFilter,
        DjangoFilterBackend,
        filters.OrderingFilter
    ]
    model = OrgUser
    filterset_fields = []
    ordering_fields = ['created_on', 'oncall_order']

    def get_queryset(self, *args, **kwargs):

        # if self.request.user.is_superuser:
        #     return super().get_queryset(*args, **kwargs)

        return OrgUser.objects.filter(org=self.request.org)

    def update(self, request, *args, **kwargs):

        data = request.data

        if isinstance(data, QueryDict):
            return super().update(request, *args, **kwargs)

        try:
            usr = OrgUser.objects.get(pk=kwargs['pk'])
        except OrgUser.DoesNotExist:
            return Response(
                {},
                status=status.HTTP_404_NOT_FOUND
            )

        usr.first_name = data['first_name']
        usr.last_name = data['last_name']
        usr.notification_type = data['notification_type']
        usr.phone_number = data.get('phone_number', None)
        if usr.phone_number_verified_on is None and usr.phone_number:
            usr.phone_number_verified_on = datetime.utcnow()
        elif usr.phone_number is None:
            usr.phone_number_verified_on = None

        if data.get('active', None) is not None:
            usr.active = data['active']
            usr.user.is_active = data['active']

            if not usr.active:
                data['is_oncall'] = False

        if data.get('role', None) is not None:
            usr.role = data['role']

        if data.get('is_oncall', None) is not None:
            usr.is_oncall = data['is_oncall']

            if usr.is_oncall:
                schedule.add_user_to_schedule(usr, request.org)
            else:
                schedule.remove_user_from_schedule(usr, request.org)

        usr.save()
        usr.user.save()

        return Response(
            OrgUserSerializer(usr).data,
            status=status.HTTP_200_OK
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_invite(request, *args, **kwargs):

    invite_info = request.data

    if invite_info.get('email_address', None) is None:
        return Response(
            'Email Address is required',
            status=status.HTTP_400_BAD_REQUEST
        )

    if invite_info.get('first_name', None) is None:
        return Response(
            'First Name is required',
            status=status.HTTP_400_BAD_REQUEST
        )

    if invite_info.get('last_name', None) is None:
        return Response(
            'Last Name is required',
            status=status.HTTP_400_BAD_REQUEST
        )

    if not re.findall(
        '[a-z0-9._%+-]+@[a-z0-9.-]+.[a-z]{2,}$',
        invite_info['email_address']
    ):
        return Response(
            'The email address you provided is not valid',
            status=status.HTTP_400_BAD_REQUEST
        )

    code = ''.join([str(randrange(0, 10)) for i in range(0, 6)])
    user = User.objects.create_user(
        username=invite_info['email_address'],
        email=invite_info['email_address'],
        first_name=invite_info['first_name'],
        last_name=invite_info['last_name'],
        is_active=False
    )

    org_user = OrgUser(
        org=request.org,
        user=user,
        first_name=invite_info['first_name'],
        last_name=invite_info['last_name'],
        email_address=invite_info['email_address'],
        active=False,
        role='user',
        code=code,
        color=colors.pick_color(request.org)
    )
    org_user.save()

    host = invite_info['host']

    invite_info['org'] = request.org.id
    cache.set(code, invite_info)

    mail.send_invite_email(invite_info['email_address'], host, code)

    return Response({'code': code}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def resend_invite(request, *args, **kwargs):

    user_id = request.GET.get('id', None)
    host = request.GET.get('host', None)

    if not user_id or not host:
        return Response({}, status=status.HTTP_403_FORBIDDEN)

    usr = OrgUser.objects.filter(
        id=int(user_id)
    ).first()

    if not usr:
        return Response({}, status=status.HTTP_403_FORBIDDEN)

    cache.delete(usr.code)

    code = ''.join([str(randrange(0, 10)) for i in range(0, 6)])
    invite_info = {
        'email_address': usr.email_address,
        'first_name': usr.first_name,
        'last_name': usr.last_name,
        'org': request.org.id,
        'code': code
    }

    usr.code = code
    usr.save()

    cache.set(code, invite_info)

    mail.send_invite_email(invite_info['email_address'], host, code)

    return Response({'code': code}, status=status.HTTP_200_OK)


@api_view(['POST'])
def check_invite(request, *args, **kwargs):

    code = request.data.get('code')

    if not code:
        return Response({}, status=status.HTTP_404_NOT_FOUND)

    signup_info = cache.get(code)
    if not signup_info:
        return Response({}, status=status.HTTP_410_GONE)

    signup_info = json.loads(signup_info)

    usr = OrgUser.objects.filter(code=code).first()

    if not usr:
        return Response({}, status=status.HTTP_402_PAYMENT_REQUIRED)

    return Response(signup_info, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def finish_invite(request, *args, **kwargs):
    code = request.data.get('code')

    if not code:
        return Response({}, status=status.HTTP_403_FORBIDDEN)

    signup_info = cache.get(code)
    if not signup_info:
        return Response({}, status=status.HTTP_403_FORBIDDEN)

    signup_info = json.loads(signup_info)

    usr = OrgUser.objects.filter(code=code).first()

    if not usr:
        return Response({}, status=status.HTTP_403_FORBIDDEN)

    new_data = request.data
    usr.email_verified_on = datetime.utcnow()
    usr.role = 'user'
    usr.is_oncall = False
    usr.active = True
    usr.code = None
    if new_data.get('phone_number'):
        usr.phone_number = new_data.get('phone_number')
        usr.phone_number_verified_on = datetime.utcnow()

    usr.user.set_password(new_data['password'])
    usr.user.is_active = True
    usr.user.save()
    usr.save()

    cache.delete(code)

    return Response({}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def update_user_order(request, *args, **kwargs):

    user_id = request.data.get('user_id')
    new_index = request.data.get('new_index')

    try:
        schedule.update_user_order(user_id, request.org, new_index)

    except OrgUser.DoesNotExist:
        return Response({}, status=status.HTTP_403_FORBIDDEN)

    return Response({}, status=status.HTTP_200_OK)


@api_view(['POST', 'GET'])
def send_notification_update(request, *args, **kwargs):

    offcall_user_id = request.data.get('offcall_id')
    oncall_user_id = request.data.get('oncall_id')

    old_user = OrgUser.objects.get(id=offcall_user_id)
    if old_user.notification_type == "email":
        mail.send_going_offcall_email(old_user.email_address)
    else:
        text.send_going_offcall(old_user.phone_number)

    current_user = OrgUser.objects.get(id=oncall_user_id)
    if current_user.notification_type == "email":
        mail.send_going_oncall_email(current_user.email_address)
    else:
        text.send_going_oncall(current_user.phone_number)

    return Response({}, status=status.HTTP_200_OK)
