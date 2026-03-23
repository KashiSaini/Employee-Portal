from datetime import datetime

from django.test import TestCase
from django.utils import timezone

from accounts.models import User

from .models import DailyWorkLog


class DailyWorkLogTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="attendance-user",
            email="attendance@example.com",
            password="testpass123",
            employee_id="EMPATT001",
        )

    def test_record_sign_off_uses_latest_sign_off_time(self):
        first_login = timezone.make_aware(datetime(2026, 3, 23, 9, 0))
        mistaken_sign_off = timezone.make_aware(datetime(2026, 3, 23, 12, 0))
        final_sign_off = timezone.make_aware(datetime(2026, 3, 23, 18, 30))

        work_log = DailyWorkLog.objects.create(
            user=self.user,
            work_date=first_login.date(),
            first_login=first_login,
        )

        work_log.record_sign_off(mistaken_sign_off, "office")
        work_log.refresh_from_db()

        self.assertEqual(work_log.sign_off_time, mistaken_sign_off)
        self.assertEqual(work_log.total_work_seconds, 3 * 60 * 60)
        self.assertTrue(work_log.is_signed_off)
        self.assertEqual(work_log.work_mode, "office")

        work_log.record_sign_off(final_sign_off, "office")
        work_log.refresh_from_db()

        self.assertEqual(work_log.sign_off_time, final_sign_off)
        self.assertEqual(work_log.total_work_seconds, 9 * 60 * 60 + 30 * 60)
        self.assertEqual(work_log.total_work_hours_display, "09:30")
