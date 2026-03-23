from datetime import datetime
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from attendance.models import DailyWorkLog
from claims.models import Claim
from leave_management.models import LeaveRequest, ShortLeaveRequest
from timesheet.models import Project, TimeSheetEntry
from wfh.models import WorkFromHomeRequest


class RequestValidationApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="employee",
            email="employee@example.com",
            password="testpass123",
            employee_id="EMP100",
        )
        self.project = Project.objects.create(
            name="BlueThink Portal",
            code="BTP001",
        )
        self.client.force_authenticate(user=self.user)

    def test_leave_request_rejects_end_date_before_start_date(self):
        response = self.client.post(
            reverse("api-leave-list"),
            {
                "leave_type": "casual",
                "start_date": "2026-03-23",
                "end_date": "2026-03-12",
                "reason": "Invalid range",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(LeaveRequest.objects.count(), 0)
        self.assertIn("end_date", response.data)

    def test_short_leave_rejects_end_time_not_later_than_start_time(self):
        response = self.client.post(
            reverse("api-short-leave-list"),
            {
                "leave_date": "2026-03-23",
                "start_time": "15:00:00",
                "end_time": "14:00:00",
                "reason": "Invalid time range",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ShortLeaveRequest.objects.count(), 0)
        self.assertIn("end_time", response.data)

    def test_timesheet_rejects_non_positive_hours(self):
        response = self.client.post(
            reverse("api-timesheet-list"),
            {
                "project": self.project.pk,
                "work_date": "2026-03-23",
                "hours": "0",
                "description": "Invalid hours",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(TimeSheetEntry.objects.count(), 0)
        self.assertIn("hours", response.data)

    def test_claim_rejects_non_positive_amount(self):
        response = self.client.post(
            reverse("api-claims-list"),
            {
                "claim_type": "food",
                "title": "Invalid claim",
                "amount": "0",
                "expense_date": "2026-03-23",
                "description": "Invalid amount",
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Claim.objects.count(), 0)
        self.assertIn("amount", response.data)

    def test_wfh_rejects_end_date_before_start_date(self):
        response = self.client.post(
            reverse("api-wfh-list"),
            {
                "start_date": "2026-03-23",
                "end_date": "2026-03-12",
                "reason": "Invalid range",
                "work_plan": "Complete tasks from home",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(WorkFromHomeRequest.objects.count(), 0)
        self.assertIn("end_date", response.data)


class SessionAttendanceApiTests(APITestCase):
    def setUp(self):
        self.password = "testpass123"
        self.user = User.objects.create_user(
            username="session-user",
            email="session@example.com",
            password=self.password,
            employee_id="EMP200",
        )

    def test_session_login_keeps_first_login_for_same_day(self):
        first_login = timezone.make_aware(datetime(2026, 3, 23, 9, 0))
        second_login = timezone.make_aware(datetime(2026, 3, 23, 13, 15))
        login_url = reverse("api-session-login")
        payload = {
            "employee_id": self.user.employee_id,
            "password": self.password,
            "work_mode": "office",
        }

        with patch("portal_api.session_views.timezone.localdate", return_value=first_login.date()), patch(
            "portal_api.session_views.timezone.now",
            return_value=first_login,
        ):
            response = self.client.post(login_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.logout()

        with patch("portal_api.session_views.timezone.localdate", return_value=second_login.date()), patch(
            "portal_api.session_views.timezone.now",
            return_value=second_login,
        ):
            response = self.client.post(login_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        work_log = DailyWorkLog.objects.get(user=self.user, work_date=first_login.date())
        self.assertEqual(work_log.first_login, first_login)
        self.assertEqual(work_log.work_mode, "office")

    def test_sign_off_overwrites_earlier_sign_off_for_same_day(self):
        first_login = timezone.make_aware(datetime(2026, 3, 23, 9, 0))
        mistaken_sign_off = timezone.make_aware(datetime(2026, 3, 23, 12, 0))
        final_sign_off = timezone.make_aware(datetime(2026, 3, 23, 18, 30))

        DailyWorkLog.objects.create(
            user=self.user,
            work_date=first_login.date(),
            first_login=first_login,
            work_mode="office",
        )

        self.client.force_login(self.user)
        session = self.client.session
        session["work_mode"] = "office"
        session.save()

        sign_off_url = reverse("api-session-sign-off")

        with patch("portal_api.session_views.timezone.localdate", return_value=first_login.date()), patch(
            "portal_api.session_views.timezone.now",
            return_value=mistaken_sign_off,
        ):
            response = self.client.post(sign_off_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Signed off successfully.")

        work_log = DailyWorkLog.objects.get(user=self.user, work_date=first_login.date())
        self.assertEqual(work_log.sign_off_time, mistaken_sign_off)
        self.assertEqual(work_log.total_work_seconds, 3 * 60 * 60)
        self.assertTrue(work_log.is_signed_off)

        with patch("portal_api.session_views.timezone.localdate", return_value=first_login.date()), patch(
            "portal_api.session_views.timezone.now",
            return_value=final_sign_off,
        ):
            response = self.client.post(sign_off_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Sign off updated successfully.")

        work_log.refresh_from_db()
        self.assertEqual(work_log.sign_off_time, final_sign_off)
        self.assertEqual(work_log.total_work_seconds, 9 * 60 * 60 + 30 * 60)
        self.assertEqual(work_log.total_work_hours_display, "09:30")
