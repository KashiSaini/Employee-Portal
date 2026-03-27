from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from timesheet.models import Project


class ProjectAssignment(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="employee_assignments",
    )
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_assignments",
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="project_assignments_made",
        null=True,
        blank=True,
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "employee"],
                name="unique_project_employee_assignment",
            )
        ]
        ordering = ["project__code", "employee__employee_id", "employee__username"]

    def clean(self):
        manager = self.project.team_manager
        if manager is None or not manager.team:
            raise ValidationError({"project": "Assign a team manager before assigning employees."})

        if self.employee_id == manager.id:
            raise ValidationError({"employee": "The team manager already has access to this project."})

        if self.employee.team != manager.team:
            raise ValidationError({"employee": "Employees must belong to the team manager's team."})

    def __str__(self):
        return f"{self.project.code} -> {self.employee.employee_id}"
