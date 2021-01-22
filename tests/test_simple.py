from tests.base import BaseTest, OrgFactory, OrgUserFactory
from rest_framework.test import APIClient


class TestLogin(BaseTest):

    def test_login_user(self):

        client = APIClient()
        org = OrgFactory.create()
        user = OrgUserFactory.create(org=org)

        res = client.login(
            username=user.email_address,
            password='12345'
        )

        self.assertEqual(res, True)
