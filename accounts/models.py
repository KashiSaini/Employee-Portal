from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)

    is_hr = models.BooleanField(default=False)
    is_manager = models.BooleanField(default=False)

    REQUIRED_FIELDS = ["email", "employee_id"]

    def __str__(self):
        return f"{self.employee_id} - {self.username}"