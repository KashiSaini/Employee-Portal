from django.conf import settings
from django.db import models


class EmployeeProfile(models.Model):
    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    # Personal details
    date_of_birth = models.DateField(blank=True, null=True)
    join_date = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    blood_group = models.CharField(max_length=10, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True)

    # Address details
    permanent_address = models.TextField(blank=True)
    current_address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)

    # Family details
    father_name = models.CharField(max_length=100, blank=True)
    mother_name = models.CharField(max_length=100, blank=True)
    spouse_name = models.CharField(max_length=100, blank=True)

    # Education details
    highest_qualification = models.CharField(max_length=150, blank=True)
    institute_name = models.CharField(max_length=150, blank=True)
    passing_year = models.PositiveIntegerField(blank=True, null=True)
    skills = models.TextField(blank=True, help_text="Write comma separated skills")
    bio = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile - {self.user.employee_id}"
    
    @property
    def completion_percentage(self):
        fields_to_check = [
            self.user.first_name,
            self.user.last_name,
            self.user.email,
            self.user.phone,
            self.user.department,
            self.user.designation,
            self.date_of_birth,
            self.join_date,
            self.gender,
            self.blood_group,
            self.emergency_contact_name,
            self.emergency_contact_phone,
            self.permanent_address,
            self.current_address,
            self.city,
            self.state,
            self.country,
            self.postal_code,
            self.father_name,
            self.mother_name,
            self.highest_qualification,
            self.institute_name,
            self.passing_year,
            self.skills,
            self.bio,
        ]

        filled_fields = sum(1 for value in fields_to_check if value not in (None, ""))
        return int((filled_fields / len(fields_to_check)) * 100)