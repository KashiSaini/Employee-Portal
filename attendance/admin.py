from django.contrib import admin
from .models import DailyWorkLog


@admin.register(DailyWorkLog)
class DailyWorkLogAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "work_date",
        "first_login",
        "sign_off_time",
        "total_work_seconds",
        "is_signed_off",
        "work_mode",
    )
    search_fields = ("user__username", "user__employee_id", "user__email")
    list_filter = ("work_date", "is_signed_off", "work_mode")