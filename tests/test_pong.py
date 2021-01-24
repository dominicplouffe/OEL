from tests.base import (
    BaseTest, OrgFactory, OrgUserFactory, PongFactory, PongTriggerFactory,
    AlertFactory
)
from rest_framework.test import APIClient
from api.models import Pong, PongTrigger, Failure, Result, Metric
from freezegun import freeze_time
from mock import patch
from tasks.pong import process_pong_alert
from datetime import datetime, timedelta
import pytz


class TestPong(BaseTest):

    def test_create(self):

        client = APIClient()
        org = OrgFactory.create()
        user = self.create_org_user(org)

        res = client.login(
            username=user.email_address,
            password='12345'
        )

        self.assertEqual(res, True)

        payload = {
            'name': 'Test Pong',
            'cron_desc': '30 4-23 * * *',
            "callback_url": None,
            "callback_username": "",
            "callback_password": "",
            "incident_interval": "1",
            "active": True,
            "notification_type": "team",
            "push_key": "testkey",
            "doc_link": "http://www.dplouffe.ca/doc",
            'triggers': [
                {
                    'trigger_type': 'complete_not_triggered_in',
                    'interval_value': '5',
                    'unit': 'minutes',
                },
                {
                    'trigger_type': 'start_not_triggered_in',
                    'interval_value': '5',
                    'unit': 'minutes',
                },
                {
                    'trigger_type': 'runs_less_than',
                    'interval_value': '5',
                    'unit': 'minutes',
                },
                {
                    'trigger_type': 'runs_more_than',
                    'interval_value': '5',
                    'unit': 'minutes',
                },
                {
                    'trigger_type': 'heartbeat_triggered',
                    'interval_value': '5',
                    'unit': 'minutes',
                }
            ]
        }

        res = client.post(
            '/api/pong/',
            payload,
            format='json'
        )
        pong_id = res.data['id']
        pong = Pong.objects.get(id=pong_id)
        self.assertEqual(pong.id, pong_id)

        self.assertIsNotNone(pong.task)
        self.assertIsNotNone(pong.alert)

        # Assert Ping
        self.assertEqual(pong.org.id, org.id)
        self.assertEqual(pong.name, payload['name'])
        self.assertEqual(pong.active, payload['active'])
        self.assertTrue(pong.cron_desc, payload['cron_desc'])
        self.assertTrue(pong.push_key, payload['push_key'])

        self.assertAlert(
            pong.alert,
            org,
            payload
        )

        # Assert PeriodicTask
        self.assertEqual(pong.task.args, '[%s]' % pong.id)
        self.assertEqual(pong.task.name, 'Pong: %s' % payload['name'])
        self.assertEqual(pong.task.interval.every, 1)
        self.assertEqual(pong.task.interval.period, 'minutes')

        # ---------------------------------------------
        # Assert that the triggres were inserted properly
        # ---------------------------------------------

        # Get Triggers
        pong_triggers = PongTrigger.objects.filter(pong=pong)
        self.assertEqual(len(pong_triggers), 5)

        ttypes = []
        for i, t in enumerate(pong_triggers):
            if (t.trigger_type) not in ttypes:
                ttypes.append(t.trigger_type)
            self.assertEqual(t.unit, 'minutes')
            self.assertEqual(t.interval_value, 5)

            payload['triggers'][i]['id'] = t.id
            payload['triggers'][i]['is_delete'] = False

        self.assertEqual(len(ttypes), 5)

        # ---------------------------------------------
        # Update pong with updated triggers
        # ---------------------------------------------
        payload['id'] = pong.id

        payload['triggers'][0]['is_delete'] = True
        payload['triggers'].append({
            'trigger_type': 'heartbeat_triggered',
            'interval_value': '10',
            'unit': 'hours',
            'id': None,
            'is_delete': False
        })

        res = client.put(
            '/api/pong/%s/' % pong.id,
            payload,
            format='json'
        )

        pong_triggers = PongTrigger.objects.filter(pong=pong)
        self.assertEqual(len(pong_triggers), 5)

        new_trigger = PongTrigger.objects.get(
            pong=pong,
            interval_value=10,
            unit='hours'
        )

    @patch('api.tools.mail.django_send')
    @patch('api.tools.text.sent_text_message')
    def test_fail_endpoint_email(self, m_text, m_send):
        client = APIClient()
        org = OrgFactory.create()
        user = self.create_org_user(org)

        res = client.login(
            username=user.email_address,
            password='12345'
        )

        self.assertEqual(res, True)

        alert = AlertFactory.create(org=org)
        pong = PongFactory.create(
            org=org,
            alert=alert
        )

        res = client.get(
            '/api/pongme/fail/%s' % pong.push_key
        )

        # Trigger does not exist yes, no notification should be sent
        self.assertEqual(res.data['notification_sent']['sent'], False)

        # Try to send fail again, should get a 429 status code
        res = client.get(
            '/api/pongme/fail/%s' % pong.push_key
        )
        self.assertEqual(res.status_code, 429)

        # Create new pong to bypass 429 status code
        alert = AlertFactory.create(org=org)
        pong = PongFactory.create(
            org=org,
            alert=alert
        )

        PongTriggerFactory.create(
            pong=pong,
            trigger_type='heartbeat_triggered'
        )

        res = client.get(
            '/api/pongme/fail/%s' % pong.push_key
        )

        # Now that trigger has been created, a notifiction should be sent
        self.assertEqual(res.data['notification_sent']['sent'], True)

        self.assertEqual(m_send.call_count, 1)
        self.assertEqual(
            m_send.call_args_list[0][0][0],
            'OnErrorLog Failure : %s ' % pong.name
        )
        self.assertEqual(
            m_send.call_args_list[0][0][2],
            'OnErrorLog Notification <dominic@dplouffe.ca>'
        )
        self.assertEqual(
            m_send.call_args_list[0][0][3],
            [user.email_address]
        )
        self.assertTrue(
            '<!DOCTYPE html>' in m_send.call_args_list[0][1]['html_message']
        )

        # Check Failure
        fail = Failure.objects.get(alert=pong.alert)

        self.assertEqual(fail.status_code, 500)
        self.assertEqual(fail.reason, 'heartbeat_triggered')
        self.assertEqual(fail.content, 'Hearbeat was triggered from your task')
        self.assertEqual(fail.notify_org_user.id, user.id)
        self.assertEqual(fail.recovered_on, None)

    @freeze_time("2021-01-18 00:00:00")
    @patch('api.tools.mail.django_send')
    @patch('api.tools.text.sent_text_message')
    def test_start_pong(self, m_text, m_send):
        client = APIClient()
        org = OrgFactory.create()
        user = self.create_org_user(org)

        res = client.login(
            username=user.email_address,
            password='12345'
        )

        self.assertEqual(res, True)

        alert = AlertFactory.create(org=org)
        pong = PongFactory.create(
            org=org,
            alert=alert,
            cron_desc='* 0 * * *'
        )

        PongTriggerFactory.create(
            pong=pong,
            trigger_type='start_not_triggered_in'
        )

        res = client.get(
            '/api/pongme/start/%s' % pong.push_key
        )

        # Setting a start pong time doesn't send a notification, it just
        # sets the last time the pong was started on the pong object
        self.assertEqual(res.data['notification_sent']['sent'], False)

        pong = Pong.objects.get(pk=pong.id)
        self.assertIsNotNone(pong.last_start_on)

        # Run the pong alert task... It should work, no notification should be
        # sent
        process_pong_alert(pong.id)

        fails = Failure.objects.filter(alert=pong.alert)
        self.assertEqual(fails.count(), 0)
        self.assertEqual(m_send.call_count, 0)

        # Set the last start to 5 minutes in the past.
        # No notification should be sent because there is a 60 sec
        # grace period
        pong.last_start_on = datetime.now(pytz.UTC) - timedelta(minutes=5)
        pong.save()

        process_pong_alert(pong.id)

        fails = Failure.objects.filter(alert=pong.alert)
        self.assertEqual(fails.count(), 0)
        self.assertEqual(m_send.call_count, 0)

        # Set last start date to 7 minutes in the past.
        # A notification should be sent since the last time the start
        # was hit was more than 5 minutes ago.

        pong.last_start_on = datetime.now(pytz.UTC) - timedelta(minutes=7)
        pong.save()

        process_pong_alert(pong.id)

        fails = Failure.objects.filter(alert=pong.alert)
        self.assertEqual(fails.count(), 1)
        self.assertEqual(m_send.call_count, 1)

        # Check fail
        fail = Failure.objects.get(alert=pong.alert)
        self.assertEqual(fail.status_code, 500)
        self.assertEqual(fail.reason, 'start_not_triggered')
        self.assertEqual(
            fail.content,
            'Pong Start On last triggered on:'
            ' 2021-01-17 23:53:00+00:00 - Num Seconds: 360.00'
        )
        self.assertEqual(fail.notify_org_user.id, user.id)
        self.assertEqual(fail.recovered_on, None)

        # Check that email was sent properly

        self.assertEqual(m_send.call_count, 1)
        self.assertEqual(
            m_send.call_args_list[0][0][0],
            'OnErrorLog Failure : %s ' % pong.name
        )
        self.assertEqual(
            m_send.call_args_list[0][0][2],
            'OnErrorLog Notification <dominic@dplouffe.ca>'
        )
        self.assertEqual(
            m_send.call_args_list[0][0][3],
            [user.email_address]
        )
        self.assertTrue(
            '<!DOCTYPE html>' in m_send.call_args_list[0][1]['html_message']
        )

        # ---------------------------------------------
        # Recovery
        # ---------------------------------------------
        pong.last_start_on = datetime.now(pytz.UTC) - timedelta(minutes=2)
        pong.save()

        process_pong_alert(pong.id)
        fail = Failure.objects.get(alert=pong.alert)

        self.assertIsNotNone(fail.recovered_on)
        self.assertEqual(m_send.call_count, 2)
        self.assertEqual(
            m_send.call_args_list[1][0][0],
            'OnErrorLog Success : %s ' % pong.name
        )

        # ---------------------------------------------
        # Check Results
        # ---------------------------------------------
        results = Result.objects.filter(alert=pong.alert)

        rtypes = []
        for r in results:
            if r.result_type not in rtypes:
                rtypes.append(r.result_type)

            self.assertEqual(r.count, 4)
            self.assertEqual(r.failure, 1)
            self.assertEqual(r.success, 3)

        self.assertEqual(len(rtypes), 2)

    @freeze_time("2021-01-18 00:00:00")
    @patch('api.tools.mail.django_send')
    @patch('api.tools.text.sent_text_message')
    def test_end_pong(self, m_text, m_send):
        client = APIClient()
        org = OrgFactory.create()
        user = self.create_org_user(org)

        res = client.login(
            username=user.email_address,
            password='12345'
        )

        self.assertEqual(res, True)

        alert = AlertFactory.create(org=org)
        pong = PongFactory.create(
            org=org,
            alert=alert,
            cron_desc='* 0 * * *',
            last_start_on=datetime(2021, 1, 17, 23, 55, 0)
        )

        PongTriggerFactory.create(
            pong=pong,
            trigger_type='complete_not_triggered_in'
        )

        res = client.get(
            '/api/pongme/end/%s' % pong.push_key
        )

        # Sending a complete endpoint will not send a notification
        # It will set the last_complete_on date end check the runs_more_than
        # and runs_less_than triggers
        self.assertEqual(res.data['notification_sent']['sent'], False)

        pong = Pong.objects.get(pk=pong.id)
        self.assertIsNotNone(pong.last_complete_on)
        self.assertEqual(pong.last_start_on, pong.last_start_check)

        # Run the pong alert task... It should work, no notification should be
        # sent
        process_pong_alert(pong.id)

        fails = Failure.objects.filter(alert=pong.alert)
        self.assertEqual(fails.count(), 0)
        self.assertEqual(m_send.call_count, 0)

        # Set last start date to 7 minutes in the past.
        # A notification should be sent since the last time the start
        # was hit was more than 5 minutes ago.

        pong.last_start_on = datetime.now(pytz.UTC) - timedelta(minutes=7)
        pong.save()

        process_pong_alert(pong.id)

        fails = Failure.objects.filter(alert=pong.alert)
        self.assertEqual(fails.count(), 1)
        self.assertEqual(m_send.call_count, 1)

        # Check fail
        fail = Failure.objects.get(alert=pong.alert)
        self.assertEqual(fail.status_code, 500)
        self.assertEqual(fail.reason, 'comp_not_triggered')
        self.assertEqual(
            fail.content,
            'Pong Completed On Last triggered on:'
            ' 2021-01-17 23:53:00+00:00 - Num Seconds: 360.00'
        )
        self.assertEqual(fail.notify_org_user.id, user.id)
        self.assertEqual(fail.recovered_on, None)

        # Check that email was sent properly

        self.assertEqual(m_send.call_count, 1)
        self.assertEqual(
            m_send.call_args_list[0][0][0],
            'OnErrorLog Failure : %s ' % pong.name
        )
        self.assertEqual(
            m_send.call_args_list[0][0][2],
            'OnErrorLog Notification <dominic@dplouffe.ca>'
        )
        self.assertEqual(
            m_send.call_args_list[0][0][3],
            [user.email_address]
        )
        self.assertTrue(
            '<!DOCTYPE html>' in m_send.call_args_list[0][1]['html_message']
        )

        # ---------------------------------------------
        # Recovery
        # ---------------------------------------------
        pong.last_start_on = datetime.now(pytz.UTC) - timedelta(minutes=2)
        pong.save()

        process_pong_alert(pong.id)
        fail = Failure.objects.get(alert=pong.alert)

        self.assertIsNotNone(fail.recovered_on)
        self.assertEqual(m_send.call_count, 2)
        self.assertEqual(
            m_send.call_args_list[1][0][0],
            'OnErrorLog Success : %s ' % pong.name
        )

        # ---------------------------------------------
        # Check Results
        # ---------------------------------------------
        results = Result.objects.filter(alert=pong.alert)

        rtypes = []
        for r in results:
            if r.result_type not in rtypes:
                rtypes.append(r.result_type)

            self.assertEqual(r.count, 3)
            self.assertEqual(r.failure, 1)
            self.assertEqual(r.success, 2)

        self.assertEqual(len(rtypes), 2)

        metrics = Metric.objects.filter(
            tags__category='pong', tags__id=pong.id
        )

        self.assertEqual(metrics[0].metrics['task_time'], 300.0)

    @freeze_time("2021-01-18 00:00:00")
    @patch('api.tools.mail.django_send')
    @patch('api.tools.text.sent_text_message')
    def test_runs_less_than(self, m_text, m_send):
        client = APIClient()
        org = OrgFactory.create()
        user = self.create_org_user(org)

        res = client.login(
            username=user.email_address,
            password='12345'
        )

        self.assertEqual(res, True)

        alert = AlertFactory.create(org=org)
        pong = PongFactory.create(
            org=org,
            alert=alert,
            cron_desc='* 0 * * *',
            last_start_on=datetime(2021, 1, 17, 23, 50, 0)
        )

        PongTriggerFactory.create(
            pong=pong,
            trigger_type='runs_less_than'
        )

        # send the complete end point.. It should work this time since
        # the diff from the start and end is more than 5 mins
        res = client.get(
            '/api/pongme/end/%s' % pong.push_key
        )
        self.assertEqual(res.data['notification_sent']['sent'], False)

        # Create a new pong and make it fail
        alert = AlertFactory.create(org=org)
        pong = PongFactory.create(
            org=org,
            alert=alert,
            cron_desc='* 0 * * *',
            last_start_on=datetime(2021, 1, 17, 23, 57, 0)
        )

        PongTriggerFactory.create(
            pong=pong,
            trigger_type='runs_less_than'
        )
        res = client.get(
            '/api/pongme/end/%s' % pong.push_key
        )
        self.assertEqual(res.data['notification_sent']['sent'], True)

        # Check fail
        fail = Failure.objects.get(alert=pong.alert)
        self.assertEqual(fail.status_code, 500)
        self.assertEqual(fail.reason, 'runs_less_than')
        self.assertEqual(
            fail.content,
            'Expected Seconds: 300 - Num Seconds: 180.00'
        )
        self.assertEqual(fail.notify_org_user.id, user.id)
        self.assertEqual(fail.recovered_on, None)

        # Check that email was sent properly

        self.assertEqual(m_send.call_count, 1)
        self.assertEqual(
            m_send.call_args_list[0][0][0],
            'OnErrorLog Failure : %s ' % pong.name
        )
        self.assertEqual(
            m_send.call_args_list[0][0][2],
            'OnErrorLog Notification <dominic@dplouffe.ca>'
        )
        self.assertEqual(
            m_send.call_args_list[0][0][3],
            [user.email_address]
        )
        self.assertTrue(
            '<!DOCTYPE html>' in m_send.call_args_list[0][1]['html_message']
        )

        # ---------------------------------------------
        # Check Results
        # ---------------------------------------------
        results = Result.objects.filter(alert=pong.alert)

        rtypes = []
        for r in results:
            if r.result_type not in rtypes:
                rtypes.append(r.result_type)

            self.assertEqual(r.count, 1)
            self.assertEqual(r.failure, 1)
            self.assertEqual(r.success, 0)

        self.assertEqual(len(rtypes), 2)

        metrics = Metric.objects.filter(
            tags__category='pong', tags__id=pong.id
        )

        self.assertEqual(metrics[0].metrics['task_time'], 180.0)

    @freeze_time("2021-01-18 00:00:00")
    @patch('api.tools.mail.django_send')
    @patch('api.tools.text.sent_text_message')
    def test_runs_more_than(self, m_text, m_send):
        client = APIClient()
        org = OrgFactory.create()
        user = self.create_org_user(org)

        res = client.login(
            username=user.email_address,
            password='12345'
        )

        self.assertEqual(res, True)

        alert = AlertFactory.create(org=org)
        pong = PongFactory.create(
            org=org,
            alert=alert,
            cron_desc='* 0 * * *',
            last_start_on=datetime(2021, 1, 17, 23, 57, 0)
        )

        PongTriggerFactory.create(
            pong=pong,
            trigger_type='runs_more_than'
        )

        # send the complete end point.. It should work this time since
        # the diff from the start and end is more than 5 mins
        res = client.get(
            '/api/pongme/end/%s' % pong.push_key
        )
        self.assertEqual(res.data['notification_sent']['sent'], False)

        # Create a new pong and make it fail
        alert = AlertFactory.create(org=org)
        pong = PongFactory.create(
            org=org,
            alert=alert,
            cron_desc='* 0 * * *',
            last_start_on=datetime(2021, 1, 17, 23, 53, 0)
        )

        PongTriggerFactory.create(
            pong=pong,
            trigger_type='runs_more_than'
        )
        res = client.get(
            '/api/pongme/end/%s' % pong.push_key
        )
        self.assertEqual(res.data['notification_sent']['sent'], True)

        # Check fail
        fail = Failure.objects.get(alert=pong.alert)
        self.assertEqual(fail.status_code, 500)
        self.assertEqual(fail.reason, 'runs_more_than')
        self.assertEqual(
            fail.content,
            'Expected Seconds: 300 - Num Seconds: 420.00'
        )
        self.assertEqual(fail.notify_org_user.id, user.id)
        self.assertEqual(fail.recovered_on, None)

        # Check that email was sent properly

        self.assertEqual(m_send.call_count, 1)
        self.assertEqual(
            m_send.call_args_list[0][0][0],
            'OnErrorLog Failure : %s ' % pong.name
        )
        self.assertEqual(
            m_send.call_args_list[0][0][2],
            'OnErrorLog Notification <dominic@dplouffe.ca>'
        )
        self.assertEqual(
            m_send.call_args_list[0][0][3],
            [user.email_address]
        )
        self.assertTrue(
            '<!DOCTYPE html>' in m_send.call_args_list[0][1]['html_message']
        )

        # ---------------------------------------------
        # Check Results
        # ---------------------------------------------
        results = Result.objects.filter(alert=pong.alert)

        rtypes = []
        for r in results:
            if r.result_type not in rtypes:
                rtypes.append(r.result_type)

            self.assertEqual(r.count, 1)
            self.assertEqual(r.failure, 1)
            self.assertEqual(r.success, 0)

        self.assertEqual(len(rtypes), 2)

        metrics = Metric.objects.filter(
            tags__category='pong', tags__id=pong.id
        )

        self.assertEqual(metrics[0].metrics['task_time'], 420.0)

    def test_validate_cron(self):
        client = APIClient()
        org = OrgFactory.create()
        user = self.create_org_user(org)

        res = client.login(
            username=user.email_address,
            password='12345'
        )

        self.assertEqual(res, True)

        res = client.post(
            '/api/pong/cron_check/',
            {'cron': '* 18 1 2 3'},
            format='json'
        )

        self.assertEqual(
            res.data['pretty'],
            'Every minute between 18:00 and 18:59 on the 1st'
            ' of February and on every Wednesday in February'
        )

        self.assertEqual(
            res.data['res'][0],
            ['*']
        )
        self.assertEqual(
            res.data['res'][1],
            [18]
        )
        self.assertEqual(
            res.data['res'][2],
            [1]
        )
        self.assertEqual(
            res.data['res'][3],
            [2]
        )
        self.assertEqual(
            res.data['res'][4],
            [3]
        )

        a = 0
        a += 1
