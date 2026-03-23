from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import SalarySlip, PolicyDocument, CompanyDocument


@login_required
def salary_slip_list(request):
    slips = SalarySlip.objects.filter(user=request.user, is_visible=True)
    return render(request, "documents/salary_slip_list.html", {"slips": slips})


@login_required
def policy_list(request):
    policies = PolicyDocument.objects.filter(is_active=True)
    return render(request, "documents/policy_list.html", {"policies": policies})


@login_required
def company_document_list(request):
    documents = CompanyDocument.objects.filter(is_active=True)
    return render(request, "documents/company_document_list.html", {"documents": documents})