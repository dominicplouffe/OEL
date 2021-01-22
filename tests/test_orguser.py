from tests.base import BaseTest, OrgFactory, OrgUserFactory
from rest_framework.test import APIClient
from mock import patch
from api.models import OrgUser, Schedule, Org
from django.contrib.auth.models import User
from tests import cache
import factory
from api.views import org_user
from api.common import schedule

org_user.cache = cache


class TestOrgUser(BaseTest):

    @patch('api.tools.mail.django_send')
    def test_send_invite(self, m_send):

        client = APIClient()
        org = OrgFactory.create()
        user = self.create_org_user(org)
        usertwo = self.create_org_user(org)

        res = client.login(
            username=user.email_address,
            password='12345'
        )

        self.assertEqual(res, True)

        payload = {
            'email_address': factory.Faker('email').generate(),
            'first_name': factory.Faker('first_name').generate(),
            'last_name': factory.Faker('last_name').generate(),
            'host': 'http://localhost'
        }

        res = client.post(
            '/api/auth/send-invite',
            payload,
            format='json'
        )

        self.assertEqual(res.status_code, 200)

        org_user = OrgUser.objects.get(email_address=payload['email_address'])

        self.assertEqual(org_user.email_address, payload['email_address'])
        self.assertEqual(org_user.first_name, payload['first_name'])
        self.assertEqual(org_user.last_name, payload['last_name'])
        self.assertEqual(org_user.active, False)
        self.assertEqual(org_user.email_verified_on, None)
        self.assertEqual(org_user.org.id, org.id)

        self.assertEqual(org_user.phone_number, None)
        self.assertEqual(org_user.phone_number_verified_on, None)
        self.assertEqual(org_user.notification_type, 'email')
        self.assertEqual(org_user.role, 'user')
        self.assertEqual(org_user.is_oncall, False)
        self.assertEqual(len(org_user.code), 6)
        self.assertTrue(org_user.code.isdigit())
        self.assertEqual(len(org_user.color), 7)

        # Confirm that invite email was sent properly
        self.assertEqual(m_send.call_count, 1)
        self.assertEqual(
            m_send.call_args_list[0][0][0],
            'onErrorLog: You have been invited',
        )
        self.assertEqual(
            m_send.call_args_list[0][0][2],
            'OnErrorLog Notification <dominic@dplouffe.ca>',
        )
        self.assertEqual(
            m_send.call_args_list[0][0][3],
            [payload['email_address']],
        )

        self.assertTrue(
            'http://localhost/auth/accept-invite?'
            'code=%s' % org_user.code in m_send.call_args_list[0][1][
                'html_message'
            ]
        )

        # ---------------------------------------------
        # Resend Invite
        # ---------------------------------------------
        res = client.get(
            '/api/auth/resend-invite?id=%s&host=http://localhost' % org_user.id
        )

        org_user = OrgUser.objects.get(email_address=payload['email_address'])

        self.assertEqual(m_send.call_count, 2)
        self.assertEqual(
            m_send.call_args_list[1][0][0],
            'onErrorLog: You have been invited',
        )
        self.assertEqual(
            m_send.call_args_list[1][0][2],
            'OnErrorLog Notification <dominic@dplouffe.ca>',
        )
        self.assertEqual(
            m_send.call_args_list[1][0][3],
            [payload['email_address']],
        )

        self.assertTrue(
            'http://localhost/auth/accept-invite?'
            'code=%s' % org_user.code in m_send.call_args_list[1][1][
                'html_message'
            ]
        )

        # ---------------------------------------------
        # Check Invite
        # ---------------------------------------------
        res = client.post(
            '/api/auth/check-invite',
            {'code': org_user.code},
            format='json'
        )

        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data['code'], org_user.code)
        self.assertEqual(res.data['email_address'], org_user.email_address)
        self.assertEqual(res.data['first_name'], org_user.first_name)
        self.assertEqual(res.data['last_name'], org_user.last_name)
        self.assertEqual(res.data['org'], org_user.org.id)

        # ---------------------------------------------
        # Finish Invite
        # ---------------------------------------------
        res = client.post(
            '/api/auth/finish-invite',
            {
                'code': org_user.code,
                'phone_number': '555-555-5555',
                'password': '12345'
            },
            format='json'
        )
        self.assertEqual(res.status_code, 201)

        org_user = OrgUser.objects.get(email_address=payload['email_address'])
        self.assertEqual(org_user.active, True)
        self.assertTrue(org_user.email_verified_on is not None)
        self.assertEqual(org_user.is_oncall, False)
        self.assertEqual(org_user.code, None)
        self.assertEqual(org_user.phone_number, '555-555-5555')
        self.assertTrue(org_user.phone_number_verified_on is not None)

        self.assertEqual(org_user.user.is_active, True)
        self.assertTrue(org_user.user.password is not None)

        # ---------------------------------------------
        # Recheck Invite
        # ---------------------------------------------
        res = client.post(
            '/api/auth/check-invite',
            {'code': org_user.code},
            format='json'
        )

        self.assertEqual(res.status_code, 404)

        # ---------------------------------------------
        # Set User OnCall
        # ---------------------------------------------
        payload['is_oncall'] = True
        payload['notification_type'] = 'email'
        payload['phone_number'] = '555-555-5555'

        res = client.put(
            '/api/org_user/%s/' % org_user.id,
            payload,
            format='json'
        )

        self.assertEqual(res.status_code, 200)
        org_user = OrgUser.objects.get(email_address=payload['email_address'])

        scheds = Schedule.objects.filter(org=org)
        self.assertEqual(len(scheds), 3)

        sched = Schedule.objects.get(org_user=org_user)
        self.assertEqual(sched.order, 3)

        # ---------------------------------------------
        # Test Get OnCall User
        # ---------------------------------------------
        usr = schedule.get_on_call_user(org)
        self.assertEqual(usr.email_address, user.email_address)

        org.week = 3
        org.save()

        usr = schedule.get_on_call_user(org)
        self.assertEqual(usr.email_address, org_user.email_address)

        # ---------------------------------------------
        # Change OnCall Order
        # ---------------------------------------------
        res = client.post(
            '/api/org_user/update_user_order',
            {
                'user_id': org_user.id,
                'new_index': 1
            }
        )
        self.assertEqual(res.status_code, 200)
        res = client.post(
            '/api/org_user/update_user_order',
            {
                'user_id': user.id,
                'new_index': 2
            }
        )
        res = client.post(
            '/api/org_user/update_user_order',
            {
                'user_id': usertwo.id,
                'new_index': 3
            }
        )

        usr = schedule.get_on_call_user(org)
        self.assertEqual(usr.email_address, usertwo.email_address)

        # ---------------------------------------------
        # Remove User from OnCall
        # ---------------------------------------------
        payload['is_oncall'] = False

        res = client.put(
            '/api/org_user/%s/' % org_user.id,
            payload,
            format='json'
        )

        self.assertEqual(res.status_code, 200)
        org_user = OrgUser.objects.get(email_address=payload['email_address'])

        scheds = Schedule.objects.filter(org=org)
        self.assertEqual(len(scheds), 2)

        sched = Schedule.objects.filter(org_user=org_user)
        self.assertEqual(len(sched), 0)

        org = Org.objects.get(id=org.id)
        self.assertEqual(org.week, 2)

        usr = schedule.get_on_call_user(org)
        self.assertEqual(usr.email_address, usertwo.email_address)
