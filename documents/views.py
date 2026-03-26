import calendar
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from accounts.models import User

from .forms import PublicHolidayForm, SalarySlipGenerationForm
from .models import CompanyDocument, EmployeeSalary, PolicyDocument, PublicHoliday, SalarySlip
from .services import generate_salary_slip


def _salary_management_redirect(search_query=""):
    redirect_url = reverse("salary_management")
    if search_query:
        redirect_url = f"{redirect_url}?{urlencode({'q': search_query})}"
    return redirect_url


def _salary_management_only_response(request):
    if request.user.is_superuser:
        return None

    messages.error(request, "Only superadmin users can manage employee salaries and generate salary slips.")
    return redirect("dashboard_home")


def _public_holiday_only_response(request):
    if request.user.is_superuser or getattr(request.user, "is_hr", False):
        return None

    messages.error(request, "Only superadmin and HR users can manage public holidays.")
    return redirect("dashboard_home")


@login_required
def salary_slip_list(request):
    slips = SalarySlip.objects.filter(user=request.user, is_visible=True)
    return render(
        request,
        "documents/salary_slip_list.html",
        {
            "slips": slips,
            "can_manage_salary": request.user.is_superuser,
            "can_manage_holidays": request.user.is_superuser or getattr(request.user, "is_hr", False),
        },
    )


@login_required
def salary_slip_detail(request, pk):
    slips = SalarySlip.objects.select_related("user").filter(is_visible=True)

    if not (request.user.is_superuser or getattr(request.user, "is_hr", False)):
        slips = slips.filter(user=request.user)

    slip = get_object_or_404(slips, pk=pk)
    return render(request, "documents/salary_slip_detail.html", {"slip": slip})


@login_required
def salary_management(request):
    blocked_response = _salary_management_only_response(request)
    if blocked_response:
        return blocked_response

    search_query = request.GET.get("q", "").strip()
    users = User.objects.all().order_by("employee_id", "username")

    if search_query:
        users = users.filter(
            Q(employee_id__icontains=search_query)
            | Q(username__icontains=search_query)
            | Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
            | Q(email__icontains=search_query)
        )

    today = timezone.localdate()
    generation_form = SalarySlipGenerationForm(
        request.POST or None,
        user_queryset=User.objects.all(),
        initial={"month": today.month, "year": today.year},
    )

    if request.method == "POST":
        action = request.POST.get("action")
        search_query = request.POST.get("q", "").strip()

        if action == "update_salary":
            target_user = get_object_or_404(User, pk=request.POST.get("user_id"))
            salary_value = request.POST.get("monthly_salary", "").strip()

            try:
                monthly_salary = Decimal(salary_value)
            except (InvalidOperation, TypeError):
                messages.error(request, "Enter a valid monthly salary amount.")
                return redirect(_salary_management_redirect(search_query))

            if monthly_salary <= 0:
                messages.error(request, "Monthly salary must be greater than 0.")
                return redirect(_salary_management_redirect(search_query))

            salary_config, _ = EmployeeSalary.objects.update_or_create(
                user=target_user,
                defaults={
                    "monthly_salary": monthly_salary,
                    "updated_by": request.user,
                },
            )
            display_name = target_user.get_full_name() or target_user.username
            messages.success(request, f"Saved monthly salary for {display_name}: INR {salary_config.monthly_salary}.")
            return redirect(_salary_management_redirect(search_query))

        if action in {"generate_salary_slip", "generate_all_salary_slips"}:
            if generation_form.is_valid():
                month = int(generation_form.cleaned_data["month"])
                year = generation_form.cleaned_data["year"]
                employee = generation_form.cleaned_data["employee"]
                month_label = calendar.month_name[month]

                if action == "generate_salary_slip":
                    if employee is None:
                        messages.error(request, "Choose an employee or use Generate All.")
                        return redirect(_salary_management_redirect(search_query))

                    try:
                        generate_salary_slip(employee, year, month)
                    except ValueError as exc:
                        messages.error(request, str(exc))
                    else:
                        display_name = employee.get_full_name() or employee.username
                        messages.success(request, f"Generated salary slip for {display_name} for {month_label} {year}.")
                    return redirect(_salary_management_redirect(search_query))

                salary_configs = EmployeeSalary.objects.select_related("user")
                generated_count = 0
                for salary_config in salary_configs:
                    generate_salary_slip(salary_config.user, year, month)
                    generated_count += 1

                if generated_count:
                    messages.success(request, f"Generated {generated_count} salary slip(s) for {month_label} {year}.")
                else:
                    messages.error(request, "No employee salary configurations were found to generate slips.")
                return redirect(_salary_management_redirect(search_query))

            messages.error(request, "Enter a valid month, year, and employee selection.")

    salary_configurations = {
        config.user_id: config
        for config in EmployeeSalary.objects.select_related("updated_by", "user")
    }
    employees = list(users)
    for employee in employees:
        employee.salary_config = salary_configurations.get(employee.id)

    context = {
        "employees": employees,
        "generation_form": generation_form,
        "search_query": search_query,
        "filtered_count": len(employees),
    }
    return render(request, "documents/salary_management.html", context)


@login_required
def public_holiday_list(request):
    blocked_response = _public_holiday_only_response(request)
    if blocked_response:
        return blocked_response

    form = PublicHolidayForm(request.POST or None)
    if request.method == "POST" and request.POST.get("action") == "create_holiday":
        if form.is_valid():
            holiday = form.save(commit=False)
            holiday.created_by = request.user
            holiday.save()
            messages.success(request, f"Added public holiday: {holiday.name} on {holiday.holiday_date:%d %b %Y}.")
            return redirect("public_holiday_list")

        messages.error(request, "Please correct the holiday details and try again.")

    holidays = PublicHoliday.objects.all()
    return render(request, "documents/public_holiday_list.html", {"form": form, "holidays": holidays})


@login_required
def public_holiday_delete(request, pk):
    blocked_response = _public_holiday_only_response(request)
    if blocked_response:
        return blocked_response

    holiday = get_object_or_404(PublicHoliday, pk=pk)
    if request.method == "POST":
        holiday_name = holiday.name
        holiday.delete()
        messages.success(request, f"Deleted public holiday: {holiday_name}.")
    return redirect("public_holiday_list")


@login_required
def policy_list(request):
    policies = PolicyDocument.objects.filter(is_active=True)
    return render(request, "documents/policy_list.html", {"policies": policies})


@login_required
def company_document_list(request):
    documents = CompanyDocument.objects.filter(is_active=True)
    return render(request, "documents/company_document_list.html", {"documents": documents})
