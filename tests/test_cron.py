from datetime import datetime
from freezegun import freeze_time
from api.common import cron
from tests.base import BaseTest


class TestSchedule(BaseTest):

    @freeze_time("2021-01-18 18:00:00")
    def test_schedule_change_email(self):
        cron_desc = '0 18 18 1 1'
        res = cron.is_now_ok(cron_desc)
        self.assertTrue(res)

        cron_desc = '0 18 * * *'
        res = cron.is_now_ok(cron_desc)
        self.assertTrue(res)

        cron_desc = '0 * 18 * *'
        res = cron.is_now_ok(cron_desc)
        self.assertTrue(res)

        cron_desc = '0 * * 1 *'
        res = cron.is_now_ok(cron_desc)
        self.assertTrue(res)

        cron_desc = '0 * * * 1'
        res = cron.is_now_ok(cron_desc)
        self.assertTrue(res)

        cron_desc = '0 19 18 1 1'
        res = cron.is_now_ok(cron_desc)
        self.assertFalse(res)

        cron_desc = '0 18 19 1 1'
        res = cron.is_now_ok(cron_desc)
        self.assertFalse(res)

        cron_desc = '0 18 18 2 1'
        res = cron.is_now_ok(cron_desc)
        self.assertFalse(res)

        cron_desc = '0 18 18 1 2'
        res = cron.is_now_ok(cron_desc)
        self.assertFalse(res)
