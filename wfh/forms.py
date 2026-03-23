from django import forms
from .models import WorkFromHomeRequest


class WorkFromHomeRequestForm(forms.ModelForm):
    class Meta:
        model = WorkFromHomeRequest
        fields = ["start_date", "end_date", "reason", "work_plan"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "reason": forms.Textarea(attrs={"rows": 4, "placeholder": "Why do you want to work from home?"}),
            "work_plan": forms.Textarea(attrs={"rows": 4, "placeholder": "What work will you complete while working from home?"}),
        }