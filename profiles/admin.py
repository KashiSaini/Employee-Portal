from django.contrib import admin
from .models import EmployeeProfile


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "join_date", "city", "updated_at")
    search_fields = ("user__username", "user__employee_id", "user__email", "city")
    list_filter = ("gender", "city", "state", "country")