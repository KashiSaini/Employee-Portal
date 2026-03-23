from django.urls import path
from .views import salary_slip_list, policy_list, company_document_list

urlpatterns = [
    path("salary-slips/", salary_slip_list, name="salary_slip_list"),
    path("policies/", policy_list, name="policy_list"),
    path("documents/", company_document_list, name="company_document_list"),
]