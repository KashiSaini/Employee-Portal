from django import forms


class ReviewForm(forms.Form):
    remarks = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": "Write reviewer remarks (optional)"
            }
        )
    )