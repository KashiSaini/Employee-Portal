from django.conf import settings
from django.db import models
from django.utils import timezone


class SalarySlip(models.Model):
    MONTH_CHOICES = [
        (1, "January"),
        (2, "February"),
        (3, "March"),
        (4, "April"),
        (5, "May"),
        (6, "June"),
        (7, "July"),
        (8, "August"),
        (9, "September"),
        (10, "October"),
        (11, "November"),
        (12, "December"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="salary_slips"
    )
    month = models.PositiveSmallIntegerField(choices=MONTH_CHOICES)
    year = models.PositiveIntegerField()
    file = models.FileField(upload_to="salary_slips/", blank=True, null=True)
    total_days_in_month = models.PositiveSmallIntegerField(default=0)
    paid_timesheet_days = models.PositiveSmallIntegerField(default=0)
    paid_weekend_days = models.PositiveSmallIntegerField(default=0)
    paid_public_holiday_days = models.PositiveSmallIntegerField(default=0)
    payable_days = models.PositiveSmallIntegerField(default=0)
    unpaid_days = models.PositiveSmallIntegerField(default=0)
    monthly_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    daily_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    generated_at = models.DateTimeField(default=timezone.now)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_visible = models.BooleanField(default=True)

    class Meta:
        ordering = ["-year", "-month"]
        unique_together = ("user", "month", "year")

    def __str__(self):
        return f"{self.user.employee_id} - {self.get_month_display()} {self.year}"


class EmployeeSalary(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="salary_configuration",
    )
    monthly_salary = models.DecimalField(max_digits=12, decimal_places=2)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="salary_configuration_updates",
    )

    class Meta:
        ordering = ["user__employee_id", "user__username"]

    def __str__(self):
        return f"{self.user.employee_id} - {self.monthly_salary}"


class PublicHoliday(models.Model):
    name = models.CharField(max_length=150)
    holiday_date = models.DateField(unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="public_holidays_created",
    )

    class Meta:
        ordering = ["holiday_date", "name"]

    def __str__(self):
        return f"{self.name} ({self.holiday_date:%d %b %Y})"


class PolicyDocument(models.Model):
    CATEGORY_CHOICES = [
        ("hr", "HR Policy"),
        ("leave", "Leave Policy"),
        ("attendance", "Attendance Policy"),
        ("security", "Security Policy"),
        ("it", "IT Policy"),
        ("general", "General"),
    ]

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="general")
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="policy_documents/")
    effective_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class CompanyDocument(models.Model):
    DOC_TYPE_CHOICES = [
        ("form", "Form"),
        ("template", "Template"),
        ("notice", "Notice"),
        ("handbook", "Handbook"),
        ("other", "Other"),
    ]

    title = models.CharField(max_length=200)
    doc_type = models.CharField(max_length=20, choices=DOC_TYPE_CHOICES, default="other")
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="company_documents/")
    is_active = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title
