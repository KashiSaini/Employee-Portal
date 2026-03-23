from django.contrib import admin
from .models import LeaveRequest, ShortLeaveRequest


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "leave_type",
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
    )
    list_filter = ("leave_type", "status", "start_date", "end_date")


@admin.register(ShortLeaveRequest)
class ShortLeaveRequestAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "leave_date",
        "start_time",
        "end_time",
        "status",
        "applied_at",
    )
    search_fields = (
        "user__username",
        "user__employee_id",
        "user__email",
        "reason",
    )
    list_filter = ("status", "leave_date")