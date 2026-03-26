from django import forms

from accounts.models import User

from .models import PublicHoliday, SalarySlip


class SalarySlipGenerationForm(forms.Form):
    employee = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        empty_label="All employees with configured salary",
    )
    month = forms.ChoiceField(choices=SalarySlip.MONTH_CHOICES)
    year = forms.IntegerField(min_value=2000, max_value=2100)

    def __init__(self, *args, user_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = user_queryset if user_queryset is not None else User.objects.all()
        self.fields["employee"].queryset = queryset.order_by("employee_id", "username")


class PublicHolidayForm(forms.ModelForm):
    class Meta:
        model = PublicHoliday
        fields = ["name", "holiday_date", "description"]
        widgets = {
            "holiday_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }
