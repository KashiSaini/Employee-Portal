from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=30, unique=True)
    description = models.TextField(blank=True)
    team_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="managed_projects",
        null=True,
        blank=True,
        limit_choices_to={"is_manager": True},
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class TimeSheetEntry(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="timesheet_entries"
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.PROTECT,
        related_name="timesheet_entries"
    )
    work_date = models.DateField()
    hours = models.DecimalField(max_digits=4, decimal_places=1)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    remarks = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.hours <= 0:
            raise ValidationError("Hours must be greater than 0.")
        if self.hours > 24:
            raise ValidationError("Hours cannot be more than 24.")

    def __str__(self):
        return f"{self.user.employee_id} - {self.project.name} - {self.work_date}"
