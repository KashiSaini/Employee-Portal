from django.urls import path

from .views import (
    company_document_list,
    policy_list,
    public_holiday_delete,
    public_holiday_list,
    salary_management,
    salary_slip_detail,
    salary_slip_list,
)

urlpatterns = [
    path("salary-slips/", salary_slip_list, name="salary_slip_list"),
    path("salary-slips/manage/", salary_management, name="salary_management"),
    path("salary-slips/<int:pk>/", salary_slip_detail, name="salary_slip_detail"),
    path("public-holidays/", public_holiday_list, name="public_holiday_list"),
    path("public-holidays/<int:pk>/delete/", public_holiday_delete, name="public_holiday_delete"),
    path("policies/", policy_list, name="policy_list"),
    path("documents/", company_document_list, name="company_document_list"),
]
