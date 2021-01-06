from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.password_validation import validate_password
from api.tools.generic_domains import generic_domains
from oel.settings import ALLOW_GENERIC_EMAILS
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from api.views.org_user import OrgUserSerializer
from rest_framework.views import APIView
from rest_framework import status
from api.models import Org, OrgUser
from api.tools import mail, colors, cache
from api.common import schedule
from random import randrange
from datetime import datetime
import json
import uuid
import re

from api.serializers import UserSerializer, ChangePasswordSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    serializer = UserSerializer(
        request.user,
        context={'request': request}
    )

    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_role(request):
    if request.org_user is None:
        return Response(status=status.HTTP_403_FORBIDDEN)

    return Response(OrgUserSerializer(
        request.org_user
    ).data)


@api_view(['POST'])
def signup_process_one(request):

    signup_info = request.data

    if 'company_name' not in signup_info or 'email_address' not in signup_info:
        return Response(
            'Payload missing required field',
            status=status.HTTP_400_BAD_REQUEST
        )

    if not re.findall(
        '[a-z0-9._%+-]+@[a-z0-9.-]+.[a-z]{2,}$',
        signup_info['email_address']
    ):
        return Response(
            'The email address you provided is not valid',
            status=status.HTTP_400_BAD_REQUEST
        )

    domain = signup_info['email_address'].split('@')[-1]
    if domain in generic_domains and not ALLOW_GENERIC_EMAILS:
        return Response(
            'Please enter your company email address',
            status=status.HTTP_400_BAD_REQUEST
        )

    user_check = User.objects.filter(
        email=signup_info['email_address']
    ).first()

    if user_check:
        return Response(
            'A user with this email address already exist.',
            status=status.HTTP_400_BAD_REQUEST
        )

    code = ''.join([str(randrange(0, 10)) for i in range(0, 6)])

    host = request._current_scheme_host
    cache.set(code, signup_info)

    mail.send_confirmation_email(
        signup_info['email_address'],
        code,
        host
    )

    return Response({'status': 'ok'}, status=status.HTTP_200_OK)


@api_view(['POST'])
def signup_code_confirmation(request):

    code_info = request.data

    if 'code' not in code_info:
        return Response(
            'Payload missing required field',
            status=status.HTTP_400_BAD_REQUEST
        )

    signup_info = cache.get(code_info['code'])

    if signup_info is None:
        return Response(
            'Code you entered is invalid',
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response(signup_info, status=status.HTTP_200_OK)


@api_view(['POST'])
def signup_code_complete(request):
    code_info = request.data

    if 'code' not in code_info:
        return Response(
            'Payload missing required field',
            status=status.HTTP_400_BAD_REQUEST
        )

    if 'password' not in code_info:
        return Response(
            'Payload missing required field',
            status=status.HTTP_400_BAD_REQUEST
        )

    if 'confirmation' not in code_info:
        return Response(
            'Payload missing required field',
            status=status.HTTP_400_BAD_REQUEST
        )

    if code_info['password'] != code_info['confirmation']:
        return Response(
            'Password and confirmation must match',
            status=status.HTTP_400_BAD_REQUEST
        )

    signup_info = cache.get(code_info['code'])

    if signup_info is None:
        return Response(
            'Code you entered is invalid',
            status=status.HTTP_400_BAD_REQUEST
        )

    signup_info = json.loads(signup_info)
    user = User.objects.create_user(
        username=signup_info['email_address'],
        password=code_info['password'],
        email=signup_info['email_address'],
        first_name=code_info['first_name'],
        last_name=code_info['last_name'],
    )

    org = Org(
        name=signup_info['company_name'],
        api_key=str(uuid.uuid4())
    )
    org.save()

    org_user = OrgUser(
        org=org,
        user=user,
        first_name=code_info['first_name'],
        last_name=code_info['last_name'],
        email_address=signup_info['email_address'],
        email_verified_on=datetime.utcnow(),
        phone_number=code_info['phone_number'],
        phone_number_verified_on=datetime.utcnow(),
        active=True,
        is_oncall=True,
        color=colors.pick_color(org)
    )
    org_user.save()

    cache.delete(code_info['code'])

    schedule.add_user_to_schedule(org_user, org)

    return Response(
        OrgUserSerializer(org_user).data,
        status=status.HTTP_200_OK
    )


class ChangePasswordView(APIView):
    serializer_class = ChangePasswordSerializer
    model = User
    permission_classes = (IsAuthenticated, )

    def put(self, request, id):
        user = User.objects.filter(id=id).first()

        serializer = ChangePasswordSerializer(
            data=request.data, context={"user": user})

        if serializer.is_valid():
            new_password = serializer.data.get("password")
            user.set_password(new_password)
            user.save()
            return Response({}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
