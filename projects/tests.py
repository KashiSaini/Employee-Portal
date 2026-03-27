from datetime import date

from django.urls import reverse
from rest_framework.test import APITestCase

from accounts.models import User
from projects.models import ProjectAssignment
from timesheet.models import Project, TimeSheetEntry


class ProjectManagementAPITests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="admin",
            password="pass123",
            employee_id="EMP001",
            is_superuser=True,
            is_staff=True,
            email="admin@example.com",
        )
        self.manager = User.objects.create_user(
            username="manager",
            password="pass123",
            employee_id="EMP002",
            is_manager=True,
            team=User.TEAM_PYTHON,
            email="manager@example.com",
        )
        self.employee = User.objects.create_user(
            username="employee",
            password="pass123",
            employee_id="EMP003",
            team=User.TEAM_PYTHON,
            email="employee@example.com",
        )
        self.other_team_employee = User.objects.create_user(
            username="java-user",
            password="pass123",
            employee_id="EMP004",
            team=User.TEAM_JAVA,
            email="java@example.com",
        )
        self.project = Project.objects.create(
            name="Blue Portal",
            code="BP001",
            description="Internal portal revamp",
            team_manager=self.manager,
            is_active=True,
        )

    def test_manager_summary_only_includes_projects_assigned_to_manager(self):
        Project.objects.create(
            name="Java ERP",
            code="ERP001",
            description="Another team project",
            is_active=True,
        )
        self.client.force_authenticate(self.manager)

        response = self.client.get(reverse("api-project-management-summary"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_projects"], 1)
        self.assertEqual(response.data["projects"][0]["code"], "BP001")

    def test_manager_can_assign_same_team_members(self):
        self.client.force_authenticate(self.manager)

        response = self.client.post(
            reverse("api-project-assign-members", args=[self.project.pk]),
            {"employee_ids": [self.employee.pk]},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            ProjectAssignment.objects.filter(project=self.project, employee=self.employee).exists()
        )

    def test_manager_cannot_assign_other_team_members(self):
        self.client.force_authenticate(self.manager)

        response = self.client.post(
            reverse("api-project-assign-members", args=[self.project.pk]),
            {"employee_ids": [self.other_team_employee.pk]},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("employee_ids", response.data)

    def test_employee_timesheet_api_requires_project_assignment(self):
        unassigned_project = Project.objects.create(
            name="Unassigned Work",
            code="BP002",
            description="Not mapped to this employee",
            team_manager=self.manager,
            is_active=True,
        )
        ProjectAssignment.objects.create(
            project=self.project,
            employee=self.employee,
            assigned_by=self.manager,
        )
        self.client.force_authenticate(self.employee)

        allowed_response = self.client.post(
            reverse("api-timesheet-list"),
            {
                "project": self.project.pk,
                "work_date": date.today(),
                "hours": "8.0",
                "description": "Assigned project work",
            },
            format="json",
        )
        blocked_response = self.client.post(
            reverse("api-timesheet-list"),
            {
                "project": unassigned_project.pk,
                "work_date": date.today(),
                "hours": "4.0",
                "description": "Should fail",
            },
            format="json",
        )

        self.assertEqual(allowed_response.status_code, 201)
        self.assertEqual(blocked_response.status_code, 400)
        self.assertIn("project", blocked_response.data)
        self.assertEqual(TimeSheetEntry.objects.filter(user=self.employee).count(), 1)
