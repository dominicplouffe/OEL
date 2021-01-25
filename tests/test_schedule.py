from mock import patch
from datetime import datetime
from rest_framework.test import APIClient
from tests.base import BaseTest, OrgFactory, OrgUserFactory
from freezegun import freeze_time
from tasks import schedule


class TestSchedule(BaseTest):

    @freeze_time("2021-01-18 00:00:00")
    @patch('api.tools.mail.django_send')
    @patch('api.tools.text.sent_text_message')
    def test_schedule_change_email(self, m_text, m_send):

        client = APIClient()
        org = OrgFactory.create()
        user = self.create_org_user(org)
        usertwo = self.create_org_user(org)
        userthree = self.create_org_user(org)

        res = client.login(
            username=user.email_address,
            password='12345'
        )

        self.assertEqual(res, True)

        schedule.do_schedule(org)

        self.assertEqual(
            m_send.call_args_list[0][0][0],
            'onErrorLog: You are going off call'
        )
        self.assertEqual(
            m_send.call_args_list[0][0][3],
            [user.email_address]
        )

        self.assertEqual(
            m_send.call_args_list[1][0][0],
            'onErrorLog: You are going on call'
        )
        self.assertEqual(
            m_send.call_args_list[1][0][3],
            [usertwo.email_address]
        )

    @freeze_time("2021-01-18 00:00:00")
    @patch('api.tools.mail.django_send')
    @patch('api.tools.text.sent_text_message')
    def test_schedule_change_text(self, m_text, m_send):

        client = APIClient()
        org = OrgFactory.create()
        user = self.create_org_user(org, notification_type='text')
        usertwo = self.create_org_user(org, notification_type='text')
        userthree = self.create_org_user(org, notification_type='text')

        res = client.login(
            username=user.email_address,
            password='12345'
        )

        self.assertEqual(res, True)

        schedule.do_schedule(org)

        self.assertEqual(
            m_text.call_args_list[0][0][0],
            user.phone_number
        )
        self.assertEqual(
            m_text.call_args_list[0][0][1],
            'OnErrorLog: Just letting you know that your on-call'
            ' assistance is no longer needed'
        )

        self.assertEqual(
            m_text.call_args_list[1][0][0],
            usertwo.phone_number
        )
        self.assertEqual(
            m_text.call_args_list[1][0][1],
            'OnErrorLog: Just letting you know that you are going on call'
        )

    @freeze_time("2021-01-20 00:00:00")
    @patch('api.tools.mail.django_send')
    @patch('api.tools.text.sent_text_message')
    def test_schedule_override(self, m_text, m_send):

        client = APIClient()
        org = OrgFactory.create()
        user = self.create_org_user(org)
        usertwo = self.create_org_user(org)
        userthree = self.create_org_user(org)

        res = client.login(
            username=user.email_address,
            password='12345'
        )

        self.assertEqual(res, True)
        payload = {
            'org': org.id,
            'org_user': userthree.id,
            'start_date': '2021-01-20 00:00:00',
            'end_date': '2021-01-20 23:59:59',
        }
        res = client.post(
            '/api/schedule_override/',
            payload,
            format='json'
        )

        self.assertEqual(res.status_code, 201)

        schedule.do_schedule(org)

        self.assertEqual(
            m_send.call_args_list[0][0][0],
            'onErrorLog: You are going off call'
        )
        self.assertEqual(
            m_send.call_args_list[0][0][3],
            [user.email_address]
        )

        self.assertEqual(
            m_send.call_args_list[1][0][0],
            'onErrorLog: You are going on call'
        )
        self.assertEqual(
            m_send.call_args_list[1][0][3],
            [userthree.email_address]
        )

    @freeze_time("2021-01-21 00:00:00")
    @patch('api.tools.mail.django_send')
    @patch('api.tools.text.sent_text_message')
    def test_schedule_override_in_past(self, m_text, m_send):

        client = APIClient()
        org = OrgFactory.create()
        user = self.create_org_user(org)
        usertwo = self.create_org_user(org)
        userthree = self.create_org_user(org)

        res = client.login(
            username=user.email_address,
            password='12345'
        )

        self.assertEqual(res, True)
        payload = {
            'org': org.id,
            'org_user': userthree.id,
            'start_date': '2021-01-20 00:00:00',
            'end_date': '2021-01-20 23:59:59',
        }
        res = client.post(
            '/api/schedule_override/',
            payload,
            format='json'
        )

        self.assertEqual(res.status_code, 201)

        schedule.do_schedule(org)

        self.assertEqual(
            m_send.call_args_list[0][0][0],
            'onErrorLog: You are going off call'
        )
        self.assertEqual(
            m_send.call_args_list[0][0][3],
            [userthree.email_address]
        )

        self.assertEqual(
            m_send.call_args_list[1][0][0],
            'onErrorLog: You are going on call'
        )
        self.assertEqual(
            m_send.call_args_list[1][0][3],
            [user.email_address]
        )

    def test_get_oncall_user(self):
        client = APIClient()
        org = OrgFactory.create()
        user = self.create_org_user(org)
        usertwo = self.create_org_user(org)
        userthree = self.create_org_user(org)

        res = client.login(
            username=user.email_address,
            password='12345'
        )

        self.assertEqual(res, True)

        res = client.get('/api/org_user/get_on_call_user')

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['id'], user.id)

    @freeze_time("2021-01-21 00:00:00")
    @patch('api.tools.mail.django_send')
    @patch('api.tools.text.sent_text_message')
    def test_schedule_override_in_past(self, m_text, m_send):

        client = APIClient()
        org = OrgFactory.create()
        user = self.create_org_user(org)
        usertwo = self.create_org_user(org)
        userthree = self.create_org_user(org)

        res = client.login(
            username=user.email_address,
            password='12345'
        )

        self.assertEqual(res, True)

        res = client.post(
            '/api/org_user/send_notification_update',
            {
                'offcall_id': user.id,
                'oncall_id': usertwo.id,
            },
            format='json'
        )
        self.assertEqual(res.status_code, 200)

        self.assertEqual(
            m_send.call_args_list[0][0][0],
            'onErrorLog: You are going off call'
        )
        self.assertEqual(
            m_send.call_args_list[0][0][3],
            [user.email_address]
        )

        self.assertEqual(
            m_send.call_args_list[1][0][0],
            'onErrorLog: You are going on call'
        )
        self.assertEqual(
            m_send.call_args_list[1][0][3],
            [usertwo.email_address]
        )
