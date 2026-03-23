from django import forms
from .models import Claim


class ClaimForm(forms.ModelForm):
    class Meta:
        model = Claim
        fields = ["claim_type", "title", "amount", "expense_date", "description", "receipt"]
        widgets = {
            "expense_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "Write claim details"}),
        }