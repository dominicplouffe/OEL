import random
from tests.base import (
    BaseTest, OrgFactory, OrgUserFactory, AlertFactory,
    PongFactory, ResultFactory
)
from api import models
from rest_framework.test import APIClient
from datetime import datetime, timedelta
import pytz


class TestPongDetails(BaseTest):

    def test_pong_details(self):

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

        d = datetime.now(pytz.UTC)
        d = datetime(d.year, d.month, d.day)
        d = d - timedelta(days=50)

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
                result_type='day',
                count=cnt,
                success=success,
                failure=failure,
                total_time=i
            )

            d += timedelta(days=1)

        results = models.Result.objects.filter(alert=alert)
        self.assertEqual(results.count(), 50)

        res = client.get('/api/pong/details/%s/' % pong.id)
        cals = res.data['calendar']['data'][-51:][:-1]
        for i in range(0, 50):

            r = cals[i]
            if i % 3 == 0:
                self.assertEqual(r['count'], 10)
                self.assertEqual(r['success'], 9)
                self.assertEqual(r['failure'], 1)
                self.assertEqual(r['status'], 'success')
                self.assertEqual(r['text'], 'Everything looks great today')
                self.assertEqual(r['success_rate'], 0.90)
            elif i % 3 == 1:
                self.assertEqual(r['count'], 100)
                self.assertEqual(r['success'], 98)
                self.assertEqual(r['failure'], 2)
                self.assertEqual(r['status'], 'warning')
                self.assertEqual(r['text'], 'At least one failure on this day')
                self.assertEqual(r['success_rate'], 0.98)
            else:
                self.assertEqual(r['count'], 8)
                self.assertEqual(r['success'], 2)
                self.assertEqual(r['failure'], 6)
                self.assertEqual(r['status'], 'danger')
                self.assertEqual(r['text'], 'Many pongs failed on this day')
                self.assertEqual(r['success_rate'], 0.25)
