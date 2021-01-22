import os

from mock import patch
from api.models import Ping, PingHeader, Result, Failure
from tasks.ping import process_ping
from rest_framework.test import APIClient

from tests.base import BaseTest, OrgFactory, OrgUserFactory


class TestPing(BaseTest):

    def test_create_ping(self):

        client = APIClient()
        org = OrgFactory.create()
        user = OrgUserFactory.create(org=org)

        res = client.login(
            username=user.email_address,
            password='12345'
        )
        self.assertEqual(res, True)

        payload = {
            "name": "Test Monitor ABC",
            "endpoint": "https://dplouffe.ca/api/whatsmyip",
            "endpoint_username": "dplouffe",
            "endpoint_password": "redmaninjeans",
            "interval": "5",
            "status_code": "200",
            "content_type": "application/json",
            "expected_string": "headers.Auth",
            "expected_value": "True",
            "callback_url": None,
            "callback_username": "",
            "callback_password": "",
            "incident_interval": "1",
            "active": True,
            "notification_type": "team",
            "doc_link": "http://www.dplouffe.ca/doc"
        }

        res = client.post(
            '/api/ping/',
            payload,
            format='json'
        )

        # ---------------------------------------------
        # Assert and ensure that the ping was inserted correctly
        # ---------------------------------------------
        ping_id = res.data['id']
        ping = Ping.objects.get(id=ping_id)
        self.assertEqual(ping.id, ping_id)

        self.assertIsNotNone(ping.task)
        self.assertIsNotNone(ping.alert)

        # Assert Ping
        self.assertEqual(ping.org.id, org.id)
        self.assertEqual(ping.name, payload['name'])
        self.assertEqual(ping.interval, int(payload['interval']))
        self.assertEqual(ping.active, payload['active'])
        self.assertEqual(ping.status_code, int(payload['status_code']))
        self.assertTrue(ping.content_type, payload['content_type'])
        self.assertEqual(ping.expected_string, payload['expected_string'])
        self.assertEqual(ping.expected_value, payload['expected_value'])

        self.assertAlert(
            ping.alert,
            org,
            payload
        )

        # Assert PeriodicTask
        self.assertEqual(ping.task.args, '[%s]' % ping.id)
        self.assertEqual(ping.task.name, 'Ping: %s' % payload['name'])
        self.assertEqual(ping.task.interval.every, int(payload['interval']))
        self.assertEqual(ping.task.interval.period, 'minutes')

        # ---------------------------------------------
        # Insert a header and ensure it was inserted correctly
        # ---------------------------------------------

        header_pl = {
            'alert': ping.alert.id,
            'header_type': 'endpoint',
            'key': 'Auth',
            'value': 'True'
        }
        res = client.post(
            '/api/ping_header/',
            header_pl,
            format='json'
        )

        header_id = res.data['id']
        header = PingHeader.objects.get(id=header_id)

        self.assertEqual(header.alert.id, ping.alert.id)
        self.assertEqual(header.key, header_pl['key'])
        self.assertEqual(header.value, header_pl['value'])
        self.assertEqual(header.header_type, header_pl['header_type'])

        # ---------------------------------------------
        # Get Pings
        # ---------------------------------------------

        res = client.get(
            '/api/ping/'
        )
        self.assertEqual(res.data['count'], 1)
        self.assertEqual(res.data['results'][0]['id'], ping.id)

        # ---------------------------------------------
        # Update Ping
        # ---------------------------------------------

        payload = {
            'id': ping.id,
            "name": "Test Monitor ABC 1",
            "endpoint": "https://dplouffe.ca/api/whatsmyip1",
            "endpoint_username": "dplouffe1",
            "endpoint_password": "redmaninjeans1",
            "interval": "10",
            "status_code": "201",
            "content_type": "text/plain",
            "expected_string": "headers.Auth1",
            "expected_value": "True1",
            "callback_url": None,
            "callback_username": "",
            "callback_password": "",
            "incident_interval": "2",
            "active": True,
            "notification_type": "callback",
            "doc_link": "http://www.dplouffe.ca/doc1"
        }

        res = client.put(
            '/api/ping/%s/' % ping.id,
            payload,
            format='json'
        )

        self.assertEqual(res.data['id'], ping.id)
        ping = Ping.objects.get(id=ping_id)

        # Assert Ping
        self.assertEqual(ping.org.id, org.id)
        self.assertEqual(ping.name, payload['name'])
        self.assertEqual(ping.interval, int(payload['interval']))
        self.assertEqual(ping.active, payload['active'])
        self.assertEqual(ping.status_code, int(payload['status_code']))
        self.assertTrue(ping.content_type, payload['content_type'])
        self.assertEqual(ping.expected_string, payload['expected_string'])
        self.assertEqual(ping.expected_value, payload['expected_value'])

        self.assertAlert(
            ping.alert,
            org,
            payload
        )

        # Assert PeriodicTask
        self.assertEqual(ping.task.args, '[%s]' % ping.id)
        self.assertEqual(ping.task.interval.every, int(payload['interval']))
        self.assertEqual(ping.task.interval.period, 'minutes')

    @patch('tasks.ping.requests.get')
    def test_ping_test_happy(self, m_get):

        def j():
            return {"headers": {"Auth": "True"}}

        m_get.return_value.status_code = 200
        m_get.return_value.json = j
        m_get.return_value.content = "abc".encode()

        client = APIClient()
        org = OrgFactory.create()
        user = OrgUserFactory.create(org=org)

        res = client.login(
            username=user.email_address,
            password='12345'
        )
        self.assertEqual(res, True)

        payload = {
            'endpoint': 'https://www.dplouffe.ca/api/whatsmyiap',
            'expected_str': 'headers.Auth',
            'expected_value': 'True',
            'content_type': 'application/json',
            'status_code': 200,
            'username': 'dplouffe',
            'password': 'redmaninjeans',
            'headers': {
                'Auth': 'True'
            }
        }

        res = client.post(
            '/api/ping-test/',
            payload,
            format='json'
        )

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['check_status'], True)

        payload = {
            'endpoint': 'https://www.dplouffe.ca/api/whatsmyiap',
            'expected_str': '',
            'expected_value': 'abc',
            'content_type': 'text/plain',
            'status_code': 200,
            'username': 'dplouffe',
            'password': 'redmaninjeans',
            'headers': {
                'Auth': 'True'
            }
        }

        res = client.post(
            '/api/ping-test/',
            payload,
            format='json'
        )

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['check_status'], True)

    @patch('tasks.ping.requests.get')
    def test_ping_test_bad_status(self, m_get):

        def j():
            return {"headers": {"Auth": "Truee"}}

        m_get.return_value.status_code = 200
        m_get.return_value.json = j
        m_get.return_value.content = "abc".encode()

        client = APIClient()
        org = OrgFactory.create()
        user = OrgUserFactory.create(org=org)

        res = client.login(
            username=user.email_address,
            password='12345'
        )
        self.assertEqual(res, True)

        # Invalid key/VALUE pair
        payload = {
            'endpoint': 'https://www.dplouffe.ca/api/whatsmyiap',
            'expected_str': 'headers.Auth',
            'expected_value': 'True',
            'content_type': 'application/json',
            'status_code': 200,
            'username': 'dplouffe',
            'password': 'redmaninjeans',
            'headers': {
                'Auth': 'True'
            }
        }

        res = client.post(
            '/api/ping-test/',
            payload,
            format='json'
        )

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['check_status'], False)
        self.assertEqual(res.data['reason'], 'value_error')

        # Invalid KEY/value pair
        payload = {
            'endpoint': 'https://www.dplouffe.ca/api/whatsmyiap',
            'expected_str': 'headers.Autha',
            'expected_value': 'Truee',
            'content_type': 'application/json',
            'status_code': 200,
            'username': 'dplouffe',
            'password': 'redmaninjeans',
            'headers': {
                'Auth': 'True'
            }
        }

        res = client.post(
            '/api/ping-test/',
            payload,
            format='json'
        )

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['check_status'], False)
        self.assertEqual(res.data['reason'], 'key_error')

        # Invalid Text
        payload = {
            'endpoint': 'https://www.dplouffe.ca/api/whatsmyiap',
            'expected_str': '',
            'expected_value': 'bbbb',
            'content_type': 'text/plain',
            'status_code': 200,
            'username': 'dplouffe',
            'password': 'redmaninjeans',
            'headers': {
                'Auth': 'True'
            }
        }

        res = client.post(
            '/api/ping-test/',
            payload,
            format='json'
        )

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['check_status'], False)
        self.assertEqual(res.data['reason'], 'invalid_value')

        # Invalid Status Code
        payload = {
            'endpoint': 'https://www.dplouffe.ca/api/whatsmyiap',
            'expected_str': '',
            'expected_value': 'bbbb',
            'content_type': 'text/plain',
            'status_code': 201,
            'username': 'dplouffe',
            'password': 'redmaninjeans',
            'headers': {
                'Auth': 'True'
            }
        }

        res = client.post(
            '/api/ping-test/',
            payload,
            format='json'
        )

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['check_status'], False)
        self.assertEqual(res.data['reason'], 'status_code')

    @patch('api.tools.mail.django_send')
    @patch('api.tools.text.sent_text_message')
    @patch('tasks.ping.requests.get')
    def test_process_ping_success(self, m_get, m_text, m_send):

        def j():
            return {"headers": {"Auth": "True"}}

        m_get.return_value.status_code = 200
        m_get.return_value.json = j
        m_get.return_value.content = "abc".encode()

        client = APIClient()
        org = OrgFactory.create()
        user = self.create_org_user(org)

        res = client.login(
            username=user.email_address,
            password='12345'
        )
        self.assertEqual(res, True)

        # Create the ping and header by calling the api
        payload = {
            "name": "Test Monitor ABC",
            "endpoint": "https://dplouffe.ca/api/whatsmyip",
            "endpoint_username": "dplouffe",
            "endpoint_password": "redmaninjeans",
            "interval": "5",
            "status_code": "200",
            "content_type": "application/json",
            "expected_string": "headers.Auth",
            "expected_value": "True",
            "callback_url": None,
            "callback_username": "",
            "callback_password": "",
            "incident_interval": "1",
            "active": True,
            "notification_type": "team",
            "doc_link": "http://www.dplouffe.ca/doc"
        }

        res = client.post(
            '/api/ping/',
            payload,
            format='json'
        )

        ping_id = res.data['id']
        ping = Ping.objects.get(id=ping_id)
        self.assertEqual(ping.id, ping_id)

        header_pl = {
            'alert': ping.alert.id,
            'header_type': 'endpoint',
            'key': 'Auth',
            'value': 'True'
        }
        res = client.post(
            '/api/ping_header/',
            header_pl,
            format='json'
        )

        def insert_failure_tmp(ping, reason, status_code, content, org_user):
            pass

        res = process_ping(ping_id, failure=insert_failure_tmp)

        self.assertEqual(res, False)

        results = Result.objects.filter(alert=ping.alert)
        self.assertEqual(len(results), 2)

        self.assertEqual(results[0].result_type, 'hour')
        self.assertEqual(results[0].count, 1)
        self.assertEqual(results[0].success, 1)
        self.assertEqual(results[0].failure, 0)
        self.assertTrue(results[0].total_time > 0)

        self.assertEqual(results[1].result_type, 'day')
        self.assertEqual(results[1].count, 1)
        self.assertEqual(results[1].success, 1)
        self.assertEqual(results[1].failure, 0)
        self.assertTrue(results[1].total_time > 0)

        self.assertEqual(m_send.call_count, 0)
        self.assertEqual(m_text.call_count, 0)

    @patch('api.tools.mail.django_send')
    @patch('api.tools.text.sent_text_message')
    @patch('tasks.ping.requests.get')
    def test_process_ping_failure(self, m_get, m_text, m_send):

        def j():
            return {"headers": {"Auth": "True"}}

        m_get.return_value.status_code = 200
        m_get.return_value.json = j
        m_get.return_value.content = "abc".encode()

        client = APIClient()
        org = OrgFactory.create()
        user = self.create_org_user(org)

        res = client.login(
            username=user.email_address,
            password='12345'
        )
        self.assertEqual(res, True)

        # Create the ping and header by calling the api
        payload = {
            "name": "Test Monitor ABC",
            "endpoint": "https://dplouffe.ca/api/whatsmyip",
            "endpoint_username": "dplouffe",
            "endpoint_password": "redmaninjeans",
            "interval": "5",
            "status_code": "201",
            "content_type": "application/json",
            "expected_string": "headers.Auth",
            "expected_value": "True",
            "callback_url": None,
            "callback_username": "",
            "callback_password": "",
            "incident_interval": "1",
            "active": True,
            "notification_type": "team",
            "doc_link": "http://www.dplouffe.ca/doc"
        }

        res = client.post(
            '/api/ping/',
            payload,
            format='json'
        )

        ping_id = res.data['id']
        ping = Ping.objects.get(id=ping_id)
        self.assertEqual(ping.id, ping_id)

        header_pl = {
            'alert': ping.alert.id,
            'header_type': 'endpoint',
            'key': 'Auth',
            'value': 'True'
        }
        res = client.post(
            '/api/ping_header/',
            header_pl,
            format='json'
        )

        res = process_ping(ping_id)
        self.assertEqual(res, True)

        results = Result.objects.filter(alert=ping.alert)
        self.assertEqual(len(results), 2)

        self.assertEqual(results[0].result_type, 'hour')
        self.assertEqual(results[0].count, 1)
        self.assertEqual(results[0].success, 0)
        self.assertEqual(results[0].failure, 1)
        self.assertTrue(results[0].total_time > 0)

        self.assertEqual(results[1].result_type, 'day')
        self.assertEqual(results[1].count, 1)
        self.assertEqual(results[1].success, 0)
        self.assertEqual(results[1].failure, 1)
        self.assertTrue(results[1].total_time > 0)

        # Check Failure
        fail = Failure.objects.get(alert=ping.alert)

        self.assertEqual(fail.status_code, 200)
        self.assertEqual(fail.reason, 'status_code')
        self.assertEqual(fail.content, 'abc')
        self.assertEqual(fail.notify_org_user.id, user.id)
        self.assertEqual(fail.recovered_on, None)

        self.assertEqual(m_send.call_count, 1)
        self.assertEqual(m_text.call_count, 0)

        # -----------------------------------------------------------------
        # Correct the request status code and re-process ping (success now)
        # -----------------------------------------------------------------
        m_get.return_value.status_code = 201
        res = process_ping(ping_id)
        self.assertEqual(res, False)

        results = Result.objects.filter(alert=ping.alert)
        self.assertEqual(len(results), 2)

        self.assertEqual(results[0].count, 2)
        self.assertEqual(results[0].success, 1)
        self.assertEqual(results[0].failure, 1)

        self.assertEqual(results[1].count, 2)
        self.assertEqual(results[1].success, 1)
        self.assertEqual(results[1].failure, 1)

        self.assertEqual(m_send.call_count, 2)
        self.assertEqual(m_text.call_count, 0)

        fail = Failure.objects.get(alert=ping.alert)

        self.assertIsNotNone(fail.recovered_on)
