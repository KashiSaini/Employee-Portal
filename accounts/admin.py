from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = (
        "username",
        "employee_id",
        "email",
        "team",
        "is_staff",
        "is_manager",
        "is_hr",
        "is_active",
    )

    fieldsets = UserAdmin.fieldsets + (
        ("Employee Info", {
            "fields": (
                "employee_id",
                "department",
                "designation",
                "phone",
                "team",
                "is_manager",
                "is_hr",
            )
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Employee Info", {
            "fields": (
                "employee_id",
                "department",
                "designation",
                "phone",
                "team",
                "is_manager",
                "is_hr",
            )
        }),
    )
