from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Claim(models.Model):
    CLAIM_TYPES = [
        ("travel", "Travel"),
        ("food", "Food"),
        ("internet", "Internet"),
        ("medical", "Medical"),
        ("office", "Office Expense"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="claims"
    )
    claim_type = models.CharField(max_length=20, choices=CLAIM_TYPES)
    title = models.CharField(max_length=150)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    expense_date = models.DateField()
    description = models.TextField()
    receipt = models.FileField(upload_to="claims/receipts/", blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    remarks = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)

    def clean(self):
        if self.amount <= 0:
            raise ValidationError("Claim amount must be greater than 0.")

    def __str__(self):
        return f"{self.user.employee_id} - {self.title} - {self.status}"