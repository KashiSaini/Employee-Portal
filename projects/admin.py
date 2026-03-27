from django.contrib import admin

from .models import ProjectAssignment


@admin.register(ProjectAssignment)
class ProjectAssignmentAdmin(admin.ModelAdmin):
    list_display = ("project", "employee", "assigned_by", "assigned_at")
    search_fields = (
        "project__name",
        "project__code",
        "employee__employee_id",
        "employee__username",
        "employee__first_name",
        "employee__last_name",
    )
    list_filter = ("project__team_manager", "employee__team", "assigned_at")
