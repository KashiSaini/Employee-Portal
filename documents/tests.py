from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from timesheet.models import Project, TimeSheetEntry

from .models import EmployeeSalary, PublicHoliday, SalarySlip
from .services import generate_salary_slip


class SalarySlipGenerationTests(TestCase):
    def setUp(self):
        self.superadmin = User.objects.create_superuser(
            username="salary-admin",
            email="salary-admin@example.com",
            password="testpass123",
            employee_id="EMP900",
        )
        self.employee = User.objects.create_user(
            username="salary-employee",
            email="salary-employee@example.com",
            password="testpass123",
            employee_id="EMP901",
        )
        self.project = Project.objects.create(name="Portal Project", code="PORTAL")
        EmployeeSalary.objects.create(
            user=self.employee,
            monthly_salary=Decimal("30000.00"),
            updated_by=self.superadmin,
        )

    def test_generate_salary_slip_counts_weekends_and_public_holidays_without_double_counting(self):
        for work_date in [
            "2026-04-01",
            "2026-04-02",
            "2026-04-03",
            "2026-04-06",
            "2026-04-07",
            "2026-04-08",
            "2026-04-09",
            "2026-04-10",
            "2026-04-13",
            "2026-04-15",
            "2026-04-11",
        ]:
            TimeSheetEntry.objects.create(
                user=self.employee,
                project=self.project,
                work_date=work_date,
                hours="8.0",
                description="Approved work entry",
                status="approved",
            )

        TimeSheetEntry.objects.create(
            user=self.employee,
            project=self.project,
            work_date="2026-04-16",
            hours="8.0",
            description="Pending entry should not count",
            status="pending",
        )

        PublicHoliday.objects.create(name="Ambedkar Jayanti", holiday_date="2026-04-14", created_by=self.superadmin)
        PublicHoliday.objects.create(name="Weekend Holiday", holiday_date="2026-04-12", created_by=self.superadmin)

        slip = generate_salary_slip(self.employee, 2026, 4)

        self.assertEqual(slip.total_days_in_month, 30)
        self.assertEqual(slip.paid_timesheet_days, 10)
        self.assertEqual(slip.paid_weekend_days, 8)
        self.assertEqual(slip.paid_public_holiday_days, 1)
        self.assertEqual(slip.payable_days, 19)
        self.assertEqual(slip.unpaid_days, 11)
        self.assertEqual(slip.monthly_salary, Decimal("30000.00"))
        self.assertEqual(slip.net_salary, Decimal("19000.00"))


class SalaryManagementViewTests(TestCase):
    def setUp(self):
        self.password = "testpass123"
        self.superadmin = User.objects.create_superuser(
            username="salary-superadmin",
            email="salary-superadmin@example.com",
            password=self.password,
            employee_id="EMP910",
        )
        self.hr_user = User.objects.create_user(
            username="salary-hr",
            email="salary-hr@example.com",
            password=self.password,
            employee_id="EMP911",
            is_hr=True,
        )
        self.employee = User.objects.create_user(
            username="salary-user",
            email="salary-user@example.com",
            password=self.password,
            employee_id="EMP912",
        )
        self.project = Project.objects.create(name="Salary View Project", code="SVP001")

    def test_superadmin_can_save_salary_and_generate_slip(self):
        self.client.force_login(self.superadmin)

        response = self.client.post(
            reverse("salary_management"),
            {
                "action": "update_salary",
                "user_id": self.employee.id,
                "monthly_salary": "45000.00",
                "q": "",
            },
        )

        self.assertRedirects(response, reverse("salary_management"))
        salary_config = EmployeeSalary.objects.get(user=self.employee)
        self.assertEqual(salary_config.monthly_salary, Decimal("45000.00"))

        TimeSheetEntry.objects.create(
            user=self.employee,
            project=self.project,
            work_date="2026-04-01",
            hours="8.0",
            description="Approved work entry",
            status="approved",
        )

        response = self.client.post(
            reverse("salary_management"),
            {
                "action": "generate_salary_slip",
                "employee": self.employee.id,
                "month": 4,
                "year": 2026,
                "q": "",
            },
        )

        self.assertRedirects(response, reverse("salary_management"))
        self.assertTrue(SalarySlip.objects.filter(user=self.employee, month=4, year=2026).exists())

    def test_hr_cannot_access_salary_management(self):
        self.client.force_login(self.hr_user)

        response = self.client.get(reverse("salary_management"))

        self.assertRedirects(response, reverse("dashboard_home"))


class PublicHolidayViewTests(TestCase):
    def setUp(self):
        self.password = "testpass123"
        self.superadmin = User.objects.create_superuser(
            username="holiday-admin",
            email="holiday-admin@example.com",
            password=self.password,
            employee_id="EMP920",
        )
        self.hr_user = User.objects.create_user(
            username="holiday-hr",
            email="holiday-hr@example.com",
            password=self.password,
            employee_id="EMP921",
            is_hr=True,
        )
        self.employee = User.objects.create_user(
            username="holiday-employee",
            email="holiday-employee@example.com",
            password=self.password,
            employee_id="EMP922",
        )

    def test_hr_can_add_public_holiday(self):
        self.client.force_login(self.hr_user)

        response = self.client.post(
            reverse("public_holiday_list"),
            {
                "action": "create_holiday",
                "name": "Independence Day",
                "holiday_date": "2026-08-15",
                "description": "National holiday",
            },
        )

        self.assertRedirects(response, reverse("public_holiday_list"))
        self.assertTrue(PublicHoliday.objects.filter(name="Independence Day").exists())

    def test_employee_cannot_access_public_holiday_page(self):
        self.client.force_login(self.employee)

        response = self.client.get(reverse("public_holiday_list"))

        self.assertRedirects(response, reverse("dashboard_home"))


class SalarySlipListViewTests(TestCase):
    def setUp(self):
        self.password = "testpass123"
        self.employee = User.objects.create_user(
            username="salary-list-user",
            email="salary-list-user@example.com",
            password=self.password,
            employee_id="EMP930",
        )
        self.other_employee = User.objects.create_user(
            username="salary-list-other",
            email="salary-list-other@example.com",
            password=self.password,
            employee_id="EMP931",
        )
        SalarySlip.objects.create(
            user=self.employee,
            month=4,
            year=2026,
            monthly_salary="10000.00",
            daily_salary="333.33",
            total_days_in_month=30,
            payable_days=30,
            net_salary="10000.00",
        )
        SalarySlip.objects.create(
            user=self.other_employee,
            month=5,
            year=2026,
            monthly_salary="12000.00",
            daily_salary="387.10",
            total_days_in_month=31,
            payable_days=31,
            net_salary="12000.00",
        )

    def test_employee_only_sees_own_salary_slips(self):
        self.client.force_login(self.employee)

        response = self.client.get(reverse("salary_slip_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "April")
        self.assertNotContains(response, "May")
