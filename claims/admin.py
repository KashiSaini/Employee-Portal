from django.contrib import admin
from .models import Claim


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "title",
        "claim_type",
        "amount",
        "expense_date",
        "status",
        "submitted_at",
    )
    search_fields = (
        "user__username",
        "user__employee_id",
        "user__email",
        "title",
        "description",
    )
    list_filter = ("claim_type", "status", "expense_date", "submitted_at")