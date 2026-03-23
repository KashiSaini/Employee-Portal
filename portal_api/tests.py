from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
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
