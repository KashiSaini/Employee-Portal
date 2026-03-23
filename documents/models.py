from django.conf import settings
from django.db import models


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
    file = models.FileField(upload_to="salary_slips/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_visible = models.BooleanField(default=True)

    class Meta:
        ordering = ["-year", "-month"]
        unique_together = ("user", "month", "year")

    def __str__(self):
        return f"{self.user.employee_id} - {self.get_month_display()} {self.year}"


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