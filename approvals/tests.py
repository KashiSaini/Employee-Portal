from datetime import date

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from leave_management.models import LeaveRequest


class TeamScopedApprovalViewTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="approvals-manager",
            email="approvals.manager@example.com",
            password="testpass123",
            employee_id="EMP700",
            is_manager=True,
            team=User.TEAM_JAVA,
        )
        self.java_employee = User.objects.create_user(
            username="approvals-java",
            email="approvals.java@example.com",
            password="testpass123",
            employee_id="EMP701",
            team=User.TEAM_JAVA,
        )
        self.python_employee = User.objects.create_user(
            username="approvals-python",
            email="approvals.python@example.com",
            password="testpass123",
            employee_id="EMP702",
            team=User.TEAM_PYTHON,
        )
        self.java_leave = LeaveRequest.objects.create(
            user=self.java_employee,
            leave_type="casual",
            start_date=date(2026, 3, 23),
            end_date=date(2026, 3, 23),
            reason="Java leave",
        )
        self.python_leave = LeaveRequest.objects.create(
            user=self.python_employee,
            leave_type="casual",
            start_date=date(2026, 3, 24),
            end_date=date(2026, 3, 24),
            reason="Python leave",
        )

    def test_team_manager_can_open_review_page_for_same_team(self):
        self.client.force_login(self.manager)

        response = self.client.get(reverse("review_leave", args=[self.java_leave.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.java_employee.employee_id)

    def test_team_manager_cannot_open_review_page_for_other_team(self):
        self.client.force_login(self.manager)

        response = self.client.get(reverse("review_leave", args=[self.python_leave.id]))

        self.assertEqual(response.status_code, 404)
