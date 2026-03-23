from django.contrib import admin
from .models import WorkFromHomeRequest


@admin.register(WorkFromHomeRequest)
class WorkFromHomeRequestAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "start_date",
        "end_date",
        "status",
        "applied_at",
    )
    search_fields = (
        "user__username",
        "user__employee_id",
        "user__email",
        "reason",
        "work_plan",
    )
    list_filter = ("status", "start_date", "end_date", "applied_at")