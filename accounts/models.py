from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    TEAM_JAVA = "java"
    TEAM_PYTHON = "python"
    TEAM_PHP = "php"
    TEAM_SALESFORCE = "salesforce"
    TEAM_DYNAMICS = "dynamics"
    TEAM_CHOICES = [
        (TEAM_JAVA, "Java"),
        (TEAM_PYTHON, "Python"),
        (TEAM_PHP, "PHP"),
        (TEAM_SALESFORCE, "Salesforce"),
        (TEAM_DYNAMICS, "Dynamics"),
    ]

    employee_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    team = models.CharField(max_length=20, choices=TEAM_CHOICES, blank=True, default="")

    is_hr = models.BooleanField(default=False)
    is_manager = models.BooleanField(default=False)

    REQUIRED_FIELDS = ["email", "employee_id"]

    @property
    def has_team_scope(self):
        return bool(self.is_manager and self.team)

    def __str__(self):
        return f"{self.employee_id} - {self.username}"
