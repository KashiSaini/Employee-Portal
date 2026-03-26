import calendar
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.utils import timezone

from timesheet.models import TimeSheetEntry

from .models import EmployeeSalary, PublicHoliday, SalarySlip


MONEY_QUANTIZER = Decimal("0.01")


def _month_dates(year, month):
    total_days = calendar.monthrange(year, month)[1]
    return [date(year, month, day) for day in range(1, total_days + 1)]


def calculate_salary_breakdown(user, year, month):
    salary_config = EmployeeSalary.objects.filter(user=user).first()
    if salary_config is None:
        raise ValueError("Monthly salary is not set for this employee.")

    month_dates = _month_dates(year, month)
    total_days = len(month_dates)
    weekend_dates = {current_date for current_date in month_dates if current_date.weekday() >= 5}
    holiday_dates = set(
        PublicHoliday.objects.filter(
            holiday_date__year=year,
            holiday_date__month=month,
        ).values_list("holiday_date", flat=True)
    )
    payable_public_holidays = holiday_dates - weekend_dates
    approved_timesheet_dates = set(
        TimeSheetEntry.objects.filter(
            user=user,
            status="approved",
            work_date__year=year,
            work_date__month=month,
        )
        .values_list("work_date", flat=True)
        .distinct()
    )
    payable_timesheet_dates = approved_timesheet_dates - weekend_dates - payable_public_holidays
    payable_days = len(payable_timesheet_dates) + len(weekend_dates) + len(payable_public_holidays)
    unpaid_days = max(total_days - payable_days, 0)
    monthly_salary = salary_config.monthly_salary.quantize(MONEY_QUANTIZER, rounding=ROUND_HALF_UP)
    daily_salary = (monthly_salary / Decimal(total_days)).quantize(MONEY_QUANTIZER, rounding=ROUND_HALF_UP)

    if payable_days == total_days:
        net_salary = monthly_salary
    else:
        net_salary = (
            monthly_salary * Decimal(payable_days) / Decimal(total_days)
        ).quantize(MONEY_QUANTIZER, rounding=ROUND_HALF_UP)

    return {
        "total_days_in_month": total_days,
        "paid_timesheet_days": len(payable_timesheet_dates),
        "paid_weekend_days": len(weekend_dates),
        "paid_public_holiday_days": len(payable_public_holidays),
        "payable_days": payable_days,
        "unpaid_days": unpaid_days,
        "monthly_salary": monthly_salary,
        "daily_salary": daily_salary,
        "net_salary": net_salary,
        "generated_at": timezone.now(),
    }


def generate_salary_slip(user, year, month):
    defaults = calculate_salary_breakdown(user=user, year=year, month=month)
    slip, _ = SalarySlip.objects.update_or_create(
        user=user,
        year=year,
        month=month,
        defaults=defaults,
    )
    return slip
