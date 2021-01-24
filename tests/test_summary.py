from tests.base import (
    BaseTest, OrgFactory, OrgUserFactory, PingFactory, ResultFactory,
    AlertFactory
)
from datetime import datetime, timedelta
from rest_framework.test import APIClient
from api import models
import pytz


class TestSummary(BaseTest):

    def test_summary_ping(self):

        client = APIClient()
        org = OrgFactory.create()
        user = self.create_org_user(org)

        res = client.login(
            username=user.email_address,
            password='12345'
        )

        self.assertEqual(res, True)

        for j in range(0, 3):

            active = True
            failure_count = 0
            if j == 1:
                active = False
            if j == 2:
                failure_count = 1

            alert = AlertFactory.create(
                org=org,
                active=active,
                failure_count=failure_count
            )
            ping = PingFactory.create(
                org=org,
                alert=alert,
                active=active
            )

            d = datetime.now(pytz.UTC)
            d = datetime(d.year, d.month, d.day, d.hour)
            d = d - timedelta(hours=50)

            for i in range(0, 50):

                if i % 3 == 0:
                    cnt = 10
                    success = 9
                    failure = 1
                elif i % 3 == 1:
                    cnt = 100
                    success = 98
                    failure = 2
                else:
                    cnt = 8
                    success = 2
                    failure = 6

                r = ResultFactory.create(
                    alert=alert,
                    result_date=d,
                    result_type='hour',
                    count=cnt,
                    success=success,
                    failure=failure,
                    total_time=i
                )

                d += timedelta(hours=1)

            results = models.Result.objects.filter(alert=alert)
            self.assertEqual(results.count(), 50)

        res = client.get('/api/alert_summary/ping/')

        self.assertEqual(
            res.data['totals'],
            {'active': 2, 'down': 1, 'paused': 1, 'total': 3, 'up': 2}
        )

        self.assertEqual(res.data['objects'][0]['status'], True)
        self.assertEqual(res.data['objects'][0]['count'], 944)
        self.assertEqual(res.data['objects'][0]['success'], 872)
        self.assertEqual(res.data['objects'][0]['failure'], 72)
        self.assertEqual(res.data['objects'][0]['total_time'], 900.0)
        self.assertTrue(res.data['objects'][0]['avg_resp'] > 0.95)
        self.assertEqual(res.data['objects'][0]['downtime'], 21600)
        self.assertEqual(res.data['objects'][0]['downtime_s'], '6h 0m')
        self.assertEqual(res.data['objects'][0]['availability'], 92.37)

        self.assertEqual(res.data['objects'][1]['status'], False)
        self.assertEqual(res.data['objects'][2]['status'], True)

    def test_summary_ping_single(self):

        client = APIClient()
        org = OrgFactory.create()
        user = self.create_org_user(org)

        res = client.login(
            username=user.email_address,
            password='12345'
        )

        self.assertEqual(res, True)

        active = True
        failure_count = 0

        alert = AlertFactory.create(
            org=org,
            active=active,
            failure_count=failure_count
        )
        ping = PingFactory.create(
            org=org,
            alert=alert,
            active=active
        )

        d = datetime.now(pytz.UTC)
        d = datetime(d.year, d.month, d.day, d.hour)
        d = d - timedelta(hours=50)

        for i in range(0, 50):

            if i % 3 == 0:
                cnt = 10
                success = 9
                failure = 1
            elif i % 3 == 1:
                cnt = 100
                success = 98
                failure = 2
            else:
                cnt = 8
                success = 2
                failure = 6

            r = ResultFactory.create(
                alert=alert,
                result_date=d,
                result_type='hour',
                count=cnt,
                success=success,
                failure=failure,
                total_time=i
            )

            d += timedelta(hours=1)

        results = models.Result.objects.filter(alert=alert)
        self.assertEqual(results.count(), 50)

        res = client.get('/api/alert_summary/ping/%s/' % ping.id)

        self.assertEqual(
            res.data['totals'],
            {'active': 1, 'down': 0, 'paused': 0, 'total': 1, 'up': 1}
        )

        self.assertEqual(res.data['objects'][0]['status'], True)
        self.assertEqual(res.data['objects'][0]['count'], 944)
        self.assertEqual(res.data['objects'][0]['success'], 872)
        self.assertEqual(res.data['objects'][0]['failure'], 72)
        self.assertEqual(res.data['objects'][0]['total_time'], 900.0)
        self.assertTrue(res.data['objects'][0]['avg_resp'] > 0.95)
        self.assertEqual(res.data['objects'][0]['downtime'], 21600)
        self.assertEqual(res.data['objects'][0]['downtime_s'], '6h 0m')
        self.assertEqual(res.data['objects'][0]['availability'], 92.37)

    def test_summary_ping_single_with_filter(self):

        client = APIClient()
        org = OrgFactory.create()
        user = self.create_org_user(org)

        res = client.login(
            username=user.email_address,
            password='12345'
        )

        self.assertEqual(res, True)

        active = True
        failure_count = 0

        alert = AlertFactory.create(
            org=org,
            active=active,
            failure_count=failure_count
        )
        ping = PingFactory.create(
            org=org,
            alert=alert,
            active=active
        )

        d = datetime.now(pytz.UTC)
        d = datetime(d.year, d.month, d.day, d.hour)
        d = d - timedelta(hours=50)

        for i in range(0, 50):

            if i % 3 == 0:
                cnt = 10
                success = 9
                failure = 1
            elif i % 3 == 1:
                cnt = 100
                success = 98
                failure = 2
            else:
                cnt = 8
                success = 2
                failure = 6

            r = ResultFactory.create(
                alert=alert,
                result_date=d,
                result_type='hour',
                count=cnt,
                success=success,
                failure=failure,
                total_time=i
            )

            d += timedelta(hours=1)

        results = models.Result.objects.filter(alert=alert)
        self.assertEqual(results.count(), 50)

        res = client.get(
            '/api/alert_summary/ping/?filter=status_code=200'
        )

        self.assertEqual(
            res.data['totals'],
            {'active': 1, 'down': 0, 'paused': 0, 'total': 1, 'up': 1}
        )

        self.assertEqual(res.data['objects'][0]['status'], True)
        self.assertEqual(res.data['objects'][0]['count'], 944)
        self.assertEqual(res.data['objects'][0]['success'], 872)
        self.assertEqual(res.data['objects'][0]['failure'], 72)
        self.assertEqual(res.data['objects'][0]['total_time'], 900.0)
        self.assertTrue(res.data['objects'][0]['avg_resp'] > 0.95)
        self.assertEqual(res.data['objects'][0]['downtime'], 21600)
        self.assertEqual(res.data['objects'][0]['downtime_s'], '6h 0m')
        self.assertEqual(res.data['objects'][0]['availability'], 92.37)
