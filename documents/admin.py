from django.contrib import admin
from .models import CompanyDocument, EmployeeSalary, PolicyDocument, PublicHoliday, SalarySlip


@admin.register(SalarySlip)
class SalarySlipAdmin(admin.ModelAdmin):
    list_display = ("user", "month", "year", "net_salary", "payable_days", "is_visible", "generated_at")
    search_fields = ("user__username", "user__employee_id", "user__email")
    list_filter = ("month", "year", "is_visible")


@admin.register(EmployeeSalary)
class EmployeeSalaryAdmin(admin.ModelAdmin):
    list_display = ("user", "monthly_salary", "updated_at", "updated_by")
    search_fields = ("user__username", "user__employee_id", "user__email")


@admin.register(PublicHoliday)
class PublicHolidayAdmin(admin.ModelAdmin):
    list_display = ("name", "holiday_date", "created_by", "created_at")
    search_fields = ("name", "description")
    list_filter = ("holiday_date",)


@admin.register(PolicyDocument)
class PolicyDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "effective_date", "is_active", "uploaded_at")
    search_fields = ("title", "description")
    list_filter = ("category", "is_active")


@admin.register(CompanyDocument)
class CompanyDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "doc_type", "is_active", "uploaded_at")
    search_fields = ("title", "description")
    list_filter = ("doc_type", "is_active")
