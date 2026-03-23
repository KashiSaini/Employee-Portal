from django import forms
from .models import TimeSheetEntry, Project


class TimeSheetEntryForm(forms.ModelForm):
    class Meta:
        model = TimeSheetEntry
        fields = ["project", "work_date", "hours", "description"]
        widgets = {
            "work_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "Describe the work completed"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["project"].queryset = Project.objects.filter(is_active=True).order_by("name")