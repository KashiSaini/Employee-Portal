from django.test import TestCase
from django.urls import reverse

from .models import User


class ManageUsersViewTests(TestCase):
    def setUp(self):
        self.password = "testpass123"
        self.java_team = User.TEAM_JAVA
        self.python_team = User.TEAM_PYTHON
        self.superadmin = User.objects.create_superuser(
            username="superadmin",
            email="superadmin@example.com",
            password=self.password,
            employee_id="EMP001",
        )
        self.hr_user = User.objects.create_user(
            username="hr-user",
            email="hr@example.com",
            password=self.password,
            employee_id="EMP002",
            is_hr=True,
        )
        self.manager_user = User.objects.create_user(
            username="manager-user",
            email="manager@example.com",
            password=self.password,
            employee_id="EMP003",
            is_manager=True,
        )
        self.team_manager_user = User.objects.create_user(
            username="java-manager",
            email="java.manager@example.com",
            password=self.password,
            employee_id="EMP005",
            is_manager=True,
            team=self.java_team,
        )
        self.employee_user = User.objects.create_user(
            username="employee-user",
            email="employee@example.com",
            password=self.password,
            employee_id="EMP004",
            team=self.java_team,
        )
        self.other_team_employee = User.objects.create_user(
            username="python-user",
            email="python@example.com",
            password=self.password,
            employee_id="EMP006",
            team=self.python_team,
        )

    def test_hr_can_access_user_management_page(self):
        self.client.force_login(self.hr_user)

        response = self.client.get(reverse("manage_users"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "User Management")
        self.assertContains(response, "Create User")
        self.assertContains(response, reverse("create_user"))
        self.assertNotContains(response, "<h3>Create User</h3>", html=False)

    def test_manager_cannot_access_user_management_page(self):
        self.client.force_login(self.manager_user)

        response = self.client.get(reverse("manage_users"))

        self.assertRedirects(response, reverse("dashboard_home"))

    def test_hr_can_access_create_user_page(self):
        self.client.force_login(self.hr_user)

        response = self.client.get(reverse("create_user"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create User")

    def test_manager_cannot_access_create_user_page(self):
        self.client.force_login(self.manager_user)

        response = self.client.get(reverse("create_user"))

        self.assertRedirects(response, reverse("dashboard_home"))

    def test_team_manager_can_access_only_their_team_on_user_management_page(self):
        self.client.force_login(self.team_manager_user)

        response = self.client.get(reverse("manage_users"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.employee_user.employee_id)
        self.assertNotContains(response, self.other_team_employee.employee_id)

    def test_team_manager_can_access_create_user_page(self):
        self.client.force_login(self.team_manager_user)

        response = self.client.get(reverse("create_user"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create User")

    def test_hr_cannot_update_roles(self):
        self.client.force_login(self.hr_user)

        response = self.client.post(
            reverse("manage_users"),
            {
                "action": "update_roles",
                "user_id": self.employee_user.id,
                "is_hr": "on",
                "is_manager": "on",
                "is_superuser": "on",
            },
        )

        self.assertRedirects(response, reverse("manage_users"))
        self.employee_user.refresh_from_db()
        self.assertFalse(self.employee_user.is_hr)
        self.assertFalse(self.employee_user.is_manager)
        self.assertFalse(self.employee_user.is_superuser)
        self.assertFalse(self.employee_user.is_staff)

    def test_hr_created_users_remain_employees(self):
        self.client.force_login(self.hr_user)

        response = self.client.post(
            reverse("create_user"),
            {
                "employee_id": "EMP100",
                "username": "new-employee",
                "first_name": "New",
                "last_name": "Employee",
                "email": "new.employee@example.com",
                "department": "Operations",
                "designation": "Executive",
                "phone": "1234567890",
                "team": self.java_team,
                "password1": "strongpass123",
                "password2": "strongpass123",
                "is_hr": "on",
                "is_manager": "on",
                "is_superuser": "on",
            },
        )

        self.assertRedirects(response, f"{reverse('manage_users')}?q=EMP100")
        created_user = User.objects.get(employee_id="EMP100")
        self.assertFalse(created_user.is_hr)
        self.assertFalse(created_user.is_manager)
        self.assertFalse(created_user.is_superuser)
        self.assertFalse(created_user.is_staff)
        self.assertEqual(created_user.team, self.java_team)

    def test_superadmin_can_create_user_with_roles(self):
        self.client.force_login(self.superadmin)

        response = self.client.post(
            reverse("create_user"),
            {
                "employee_id": "EMP101",
                "username": "new-admin",
                "first_name": "Portal",
                "last_name": "Admin",
                "email": "portal.admin@example.com",
                "department": "HR",
                "designation": "Lead",
                "phone": "1234567890",
                "team": self.python_team,
                "password1": "strongpass123",
                "password2": "strongpass123",
                "is_hr": "on",
                "is_manager": "on",
                "is_superuser": "on",
            },
        )

        self.assertRedirects(response, f"{reverse('manage_users')}?q=EMP101")
        created_user = User.objects.get(employee_id="EMP101")
        self.assertTrue(created_user.is_hr)
        self.assertTrue(created_user.is_manager)
        self.assertTrue(created_user.is_superuser)
        self.assertTrue(created_user.is_staff)
        self.assertEqual(created_user.team, self.python_team)

    def test_team_manager_cannot_create_user_for_another_team(self):
        self.client.force_login(self.team_manager_user)

        response = self.client.post(
            reverse("create_user"),
            {
                "employee_id": "EMP102",
                "username": "python-new-user",
                "first_name": "Python",
                "last_name": "User",
                "email": "python.new@example.com",
                "department": "Engineering",
                "designation": "Developer",
                "phone": "1234567890",
                "team": self.python_team,
                "password1": "strongpass123",
                "password2": "strongpass123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(employee_id="EMP102").exists())
        self.assertContains(response, "Select a valid choice")

    def test_team_manager_can_create_user_for_own_team(self):
        self.client.force_login(self.team_manager_user)

        response = self.client.post(
            reverse("create_user"),
            {
                "employee_id": "EMP103",
                "username": "java-new-user",
                "first_name": "Java",
                "last_name": "User",
                "email": "java.new@example.com",
                "department": "Engineering",
                "designation": "Developer",
                "phone": "1234567890",
                "team": self.java_team,
                "password1": "strongpass123",
                "password2": "strongpass123",
            },
        )

        self.assertRedirects(response, f"{reverse('manage_users')}?q=EMP103")
        created_user = User.objects.get(employee_id="EMP103")
        self.assertEqual(created_user.team, self.java_team)
        self.assertFalse(created_user.is_manager)
        self.assertFalse(created_user.is_hr)
        self.assertFalse(created_user.is_superuser)

    def test_superadmin_can_update_existing_roles(self):
        self.client.force_login(self.superadmin)

        response = self.client.post(
            reverse("manage_users"),
            {
                "action": "update_roles",
                "user_id": self.employee_user.id,
                "is_hr": "on",
                "is_manager": "on",
                "is_superuser": "on",
                "team": self.java_team,
            },
        )

        self.assertRedirects(response, reverse("manage_users"))
        self.employee_user.refresh_from_db()
        self.assertTrue(self.employee_user.is_hr)
        self.assertTrue(self.employee_user.is_manager)
        self.assertTrue(self.employee_user.is_superuser)
        self.assertTrue(self.employee_user.is_staff)
        self.assertEqual(self.employee_user.team, self.java_team)

    def test_superadmin_can_remove_superadmin_role_from_another_user(self):
        other_superadmin = User.objects.create_superuser(
            username="other-superadmin",
            email="other.superadmin@example.com",
            password=self.password,
            employee_id="EMP007",
        )
        self.client.force_login(self.superadmin)

        response = self.client.post(
            reverse("manage_users"),
            {
                "action": "update_roles",
                "user_id": other_superadmin.id,
            },
        )

        self.assertRedirects(response, reverse("manage_users"))
        other_superadmin.refresh_from_db()
        self.assertFalse(other_superadmin.is_superuser)
        self.assertFalse(other_superadmin.is_staff)
        self.assertFalse(other_superadmin.is_hr)
        self.assertFalse(other_superadmin.is_manager)

    def test_superadmin_cannot_remove_own_superadmin_access(self):
        self.client.force_login(self.superadmin)

        response = self.client.post(
            reverse("manage_users"),
            {
                "action": "update_roles",
                "user_id": self.superadmin.id,
            },
        )

        self.assertRedirects(response, reverse("manage_users"))
        self.superadmin.refresh_from_db()
        self.assertTrue(self.superadmin.is_superuser)
        self.assertTrue(self.superadmin.is_staff)
