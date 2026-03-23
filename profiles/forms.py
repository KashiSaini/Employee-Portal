from django import forms
from .models import EmployeeProfile


class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    phone = forms.CharField(max_length=15, required=False)
    department = forms.CharField(max_length=100, required=False)
    designation = forms.CharField(max_length=100, required=False)

    class Meta:
        model = EmployeeProfile
        fields = [
            "date_of_birth",
            "join_date",
            "gender",
            "blood_group",
            "emergency_contact_name",
            "emergency_contact_phone",
            "permanent_address",
            "current_address",
            "city",
            "state",
            "country",
            "postal_code",
            "father_name",
            "mother_name",
            "spouse_name",
            "highest_qualification",
            "institute_name",
            "passing_year",
            "skills",
            "bio",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "join_date": forms.DateInput(attrs={"type": "date"}),
            "permanent_address": forms.Textarea(attrs={"rows": 3}),
            "current_address": forms.Textarea(attrs={"rows": 3}),
            "skills": forms.Textarea(attrs={"rows": 3}),
            "bio": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        user = self.instance.user if self.instance and self.instance.pk else None
        if user:
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name
            self.fields["email"].initial = user.email
            self.fields["phone"].initial = user.phone
            self.fields["department"].initial = user.department
            self.fields["designation"].initial = user.designation

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user

        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        user.email = self.cleaned_data.get("email", "")
        user.phone = self.cleaned_data.get("phone", "")
        user.department = self.cleaned_data.get("department", "")
        user.designation = self.cleaned_data.get("designation", "")

        if commit:
            user.save()
            profile.save()

        return profile