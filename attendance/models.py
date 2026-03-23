from django.conf import settings
from django.db import models


class DailyWorkLog(models.Model):
    WORK_MODE_CHOICES = [
        ("office", "Work From Office"),
        ("home", "Work From Home"),
        ("", "Not Selected"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="daily_work_logs"
    )
    work_date = models.DateField()
    first_login = models.DateTimeField()
    sign_off_time = models.DateTimeField(blank=True, null=True)
    total_work_seconds = models.PositiveIntegerField(default=0)
    work_mode = models.CharField(max_length=20, choices=WORK_MODE_CHOICES, blank=True, default="")
    is_signed_off = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "work_date")
        ordering = ["-work_date"]

    def __str__(self):
        return f"{self.user.employee_id} - {self.work_date}"

    @property
    def total_work_hours_display(self):
        hours = self.total_work_seconds // 3600
        minutes = (self.total_work_seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"