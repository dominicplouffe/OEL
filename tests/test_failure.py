from tests.base import (
    BaseTest, OrgFactory, OrgUserFactory, FailureFactory,
    AlertFactory, PingFactory
)
from api import models
from rest_framework.test import APIClient


class TestFailure(BaseTest):

    def test_status_change(self):

        client = APIClient()
        org = OrgFactory.create()
        user = self.create_org_user(org)

        res = client.login(
            username=user.email_address,
            password='12345'
        )

        self.assertEqual(res, True)
        alert = AlertFactory.create(org=org)
        ping = PingFactory.create(
            org=org,
            alert=alert
        )

        fail = FailureFactory.create(
            alert=alert,
            status_code=200,
            reason='status_code',
            notify_org_user=user,
            content='abc',
        )

        res = client.get('/api/ping/acknowledge/%s/' % fail.id)
        self.assertEqual(res.status_code, 200)
        fail = models.Failure.objects.get(pk=fail.id)
        self.assertIsNotNone(fail.acknowledged_on)
        self.assertEqual(fail.acknowledged_by.id, user.id)

        res = client.get('/api/ping/fix/%s/' % fail.id)
        self.assertEqual(res.status_code, 200)
        fail = models.Failure.objects.get(pk=fail.id)
        self.assertIsNotNone(fail.fixed_on)
        self.assertEqual(fail.fixed_by.id, user.id)

        res = client.get('/api/ping/ignore/%s/' % fail.id)
        self.assertEqual(res.status_code, 200)
        fail = models.Failure.objects.get(pk=fail.id)
        self.assertIsNotNone(fail.ignored_on)
        self.assertEqual(fail.ignored_by.id, user.id)

        # ---------------------------------------------
        # Test 404
        # ---------------------------------------------
        res = client.get('/api/ping/acknowledge/99999/')
        self.assertEqual(res.status_code, 404)
        res = client.get('/api/ping/fix/99999/')
        self.assertEqual(res.status_code, 404)
        res = client.get('/api/ping/ignore/99999/')
        self.assertEqual(res.status_code, 404)
