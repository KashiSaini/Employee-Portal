from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

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


class PasswordResetRequestForm(forms.Form):
    phone = forms.CharField(
        max_length=15,
        label="Phone number",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Registered phone number",
                "autocomplete": "tel",
                "inputmode": "tel",
                "autofocus": True,
            }
        ),
    )

    def clean_phone(self):
        return self.cleaned_data["phone"].strip()


class SetNewPasswordForm(forms.Form):
    otp = forms.CharField(
        min_length=6,
        max_length=6,
        label="OTP",
        widget=forms.TextInput(
            attrs={
                "placeholder": "6-digit OTP",
                "inputmode": "numeric",
                "autocomplete": "one-time-code",
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "New password",
                "autocomplete": "new-password",
            }
        ),
    )
    confirm_password = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Confirm new password",
                "autocomplete": "new-password",
            }
        ),
    )

    def clean_otp(self):
        otp = self.cleaned_data["otp"].strip()
        if not otp.isdigit():
            raise forms.ValidationError("OTP must contain only digits.")
        return otp

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password:
            try:
                validate_password(password)
            except ValidationError as exc:
                self.add_error("password", exc)

        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "Passwords do not match.")

        return cleaned_data


class PortalUserCreationForm(UserCreationForm):
    team = forms.ChoiceField(choices=User.TEAM_CHOICES, required=True, label="Team")
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
            "team",
        )

    def __init__(self, *args, allow_role_assignment=False, actor=None, **kwargs):
        self.allow_role_assignment = allow_role_assignment
        self.actor = actor
        super().__init__(*args, **kwargs)

        self.fields["employee_id"].label = "Employee ID"
        self.fields["email"].required = True
        self.fields["team"].choices = list(User.TEAM_CHOICES)

        placeholders = {
            "employee_id": "Employee ID",
            "username": "Username",
            "first_name": "First name",
            "last_name": "Last name",
            "email": "Email address",
            "department": "Department",
            "designation": "Designation",
            "phone": "Phone number",
            "team": "Team",
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

        if getattr(self.actor, "has_team_scope", False):
            self.fields["team"].choices = [(self.actor.team, self.actor.get_team_display())]
            self.fields["team"].initial = self.actor.team

    def clean_team(self):
        team = self.cleaned_data.get("team", "")

        if getattr(self.actor, "has_team_scope", False) and team != self.actor.team:
            raise forms.ValidationError("You can only create users for your own team.")

        return team

    def clean(self):
        cleaned_data = super().clean()

        if self.allow_role_assignment and cleaned_data.get("is_manager") and not cleaned_data.get("team"):
            self.add_error("team", "Team is required for managers.")

        return cleaned_data

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
