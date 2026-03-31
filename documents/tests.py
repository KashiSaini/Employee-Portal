from decimal import Decimal
from unittest.mock import call, patch

from django.core import mail
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from timesheet.models import Project, TimeSheetEntry

from .models import EmployeeSalary, PublicHoliday, SalarySlip
from .services import generate_salary_slip
from .tasks import generate_salary_slip_email_task


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

    def test_generate_salary_slip_excludes_weekends_from_payable_days(self):
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

        self.assertEqual(slip.total_days_in_month, 22)
        self.assertEqual(slip.paid_timesheet_days, 10)
        self.assertEqual(slip.paid_weekend_days, 0)
        self.assertEqual(slip.paid_public_holiday_days, 1)
        self.assertEqual(slip.payable_days, 11)
        self.assertEqual(slip.unpaid_days, 11)
        self.assertEqual(slip.monthly_salary, Decimal("30000.00"))
        self.assertEqual(slip.net_salary, Decimal("15000.00"))


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

    @patch("documents.views.generate_salary_slip_email_task.delay")
    def test_superadmin_can_save_salary_and_queue_slip_email(self, delay_mock):
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
        delay_mock.assert_called_once_with(self.employee.id, 2026, 4)
        self.assertFalse(SalarySlip.objects.filter(user=self.employee, month=4, year=2026).exists())

    @patch("documents.views.generate_salary_slip_email_task.delay")
    def test_generate_all_queues_only_employees_with_email(self, delay_mock):
        self.client.force_login(self.superadmin)

        employee_without_email = User.objects.create_user(
            username="salary-no-email",
            email="",
            password=self.password,
            employee_id="EMP913",
        )
        EmployeeSalary.objects.create(
            user=self.employee,
            monthly_salary=Decimal("45000.00"),
            updated_by=self.superadmin,
        )
        EmployeeSalary.objects.create(
            user=employee_without_email,
            monthly_salary=Decimal("22000.00"),
            updated_by=self.superadmin,
        )

        response = self.client.post(
            reverse("salary_management"),
            {
                "action": "generate_all_salary_slips",
                "month": 4,
                "year": 2026,
                "q": "",
            },
        )

        self.assertRedirects(response, reverse("salary_management"))
        self.assertEqual(delay_mock.call_args_list, [call(self.employee.id, 2026, 4)])

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

    def test_employee_can_open_salary_slip_pdf_view(self):
        self.client.force_login(self.employee)
        slip = SalarySlip.objects.get(user=self.employee, month=4, year=2026)

        response = self.client.get(reverse("salary_slip_pdf", args=[slip.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("inline;", response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"%PDF-"))


class SalarySlipEmailTaskTests(TestCase):
    def setUp(self):
        settings_override = self.settings(
            MEDIA_ROOT="media",
            EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
            DEFAULT_FROM_EMAIL="payroll@example.com",
        )
        settings_override.enable()
        self.addCleanup(settings_override.disable)

        self.superadmin = User.objects.create_superuser(
            username="salary-mail-admin",
            email="salary-mail-admin@example.com",
            password="testpass123",
            employee_id="EMP940",
        )
        self.employee = User.objects.create_user(
            username="salary-mail-employee",
            email="salary-mail-employee@example.com",
            password="testpass123",
            employee_id="EMP941",
        )
        self.project = Project.objects.create(name="Salary Mail Project", code="SMP001")
        EmployeeSalary.objects.create(
            user=self.employee,
            monthly_salary=Decimal("30000.00"),
            updated_by=self.superadmin,
        )

    def test_task_generates_pdf_file_and_sends_email(self):
        TimeSheetEntry.objects.create(
            user=self.employee,
            project=self.project,
            work_date="2026-04-01",
            hours="8.0",
            description="Approved work entry",
            status="approved",
        )

        result = generate_salary_slip_email_task.run(self.employee.id, 2026, 4)

        slip = SalarySlip.objects.get(user=self.employee, month=4, year=2026)

        self.assertEqual(result["status"], "sent")
        self.assertTrue(slip.file.name.endswith(".pdf"))

        with slip.file.open("rb") as pdf_file:
            self.assertTrue(pdf_file.read().startswith(b"%PDF-"))

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, [self.employee.email])
        self.assertEqual(message.from_email, "payroll@example.com")
        self.assertEqual(message.subject, "Salary Slip for April 2026")
        self.assertEqual(len(message.attachments), 1)

        attachment = message.attachments[0]
        filename = getattr(attachment, "filename", attachment[0])
        content = getattr(attachment, "content", attachment[1])
        mimetype = getattr(attachment, "mimetype", attachment[2])

        self.assertEqual(filename, "salary-slip-EMP941-2026-04.pdf")
        self.assertEqual(mimetype, "application/pdf")
        self.assertTrue(content.startswith(b"%PDF-"))
