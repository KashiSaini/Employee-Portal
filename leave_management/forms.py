from django import forms
from .models import LeaveRequest, ShortLeaveRequest


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ["leave_type", "start_date", "end_date", "reason"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "reason": forms.Textarea(attrs={"rows": 4, "placeholder": "Write reason for leave"}),
        }


class ShortLeaveRequestForm(forms.ModelForm):
    class Meta:
        model = ShortLeaveRequest
        fields = ["leave_date", "start_time", "end_time", "reason"]
        widgets = {
            "leave_date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
            "reason": forms.Textarea(attrs={"rows": 4, "placeholder": "Write reason for short leave"}),
        }