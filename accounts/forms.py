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
