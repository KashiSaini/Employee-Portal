from django.contrib import admin
from .models import Project, TimeSheetEntry


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active")
    search_fields = ("name", "code")
    list_filter = ("is_active",)


@admin.register(TimeSheetEntry)
class TimeSheetEntryAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "project",
        "work_date",
        "hours",
        "status",
        "created_at",
    )
    search_fields = (
        "user__username",
        "user__employee_id",
        "project__name",
        "project__code",
        "description",
    )
    list_filter = ("status", "work_date", "project")