from django.contrib import admin
from .models import SalarySlip, PolicyDocument, CompanyDocument


@admin.register(SalarySlip)
class SalarySlipAdmin(admin.ModelAdmin):
    list_display = ("user", "month", "year", "is_visible", "uploaded_at")
    search_fields = ("user__username", "user__employee_id", "user__email")
    list_filter = ("month", "year", "is_visible")


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