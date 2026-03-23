from django import forms


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