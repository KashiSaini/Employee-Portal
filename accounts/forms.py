from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class LoginForm(forms.Form):
    employee_id = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={"placeholder": "Employee ID"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Password"})
    )
    work_mode = forms.ChoiceField(
        choices=[
            ("", "Please Select"),
            ("office", "Work From Office"),
            ("home", "Work From Home"),
        ]
    )


class PortalUserCreationForm(UserCreationForm):
    is_superuser = forms.BooleanField(required=False, label="Superadmin")
    is_hr = forms.BooleanField(required=False, label="HR")
    is_manager = forms.BooleanField(required=False, label="Manager")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "employee_id",
            "username",
            "first_name",
            "last_name",
            "email",
            "department",
            "designation",
            "phone",
        )

    def __init__(self, *args, allow_role_assignment=False, **kwargs):
        self.allow_role_assignment = allow_role_assignment
        super().__init__(*args, **kwargs)

        self.fields["employee_id"].label = "Employee ID"
        self.fields["email"].required = True

        placeholders = {
            "employee_id": "Employee ID",
            "username": "Username",
            "first_name": "First name",
            "last_name": "Last name",
            "email": "Email address",
            "department": "Department",
            "designation": "Designation",
            "phone": "Phone number",
            "password1": "Password",
            "password2": "Confirm password",
        }

        for field_name, placeholder in placeholders.items():
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.setdefault("placeholder", placeholder)

        if not self.allow_role_assignment:
            self.fields.pop("is_superuser")
            self.fields.pop("is_hr")
            self.fields.pop("is_manager")

    def save(self, commit=True):
        user = super().save(commit=False)

        if self.allow_role_assignment:
            is_superuser = self.cleaned_data.get("is_superuser", False)
            user.is_superuser = is_superuser
            user.is_staff = is_superuser
            user.is_hr = self.cleaned_data.get("is_hr", False)
            user.is_manager = self.cleaned_data.get("is_manager", False)
        else:
            user.is_superuser = False
            user.is_staff = False
            user.is_hr = False
            user.is_manager = False

        if commit:
            user.save()

        return user
