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
    payable_working_days = total_days - len(weekend_dates)
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
    payable_days = len(payable_timesheet_dates) + len(payable_public_holidays)
    unpaid_days = max(payable_working_days - payable_days, 0)
    monthly_salary = salary_config.monthly_salary.quantize(MONEY_QUANTIZER, rounding=ROUND_HALF_UP)
    daily_salary = (monthly_salary / Decimal(payable_working_days)).quantize(MONEY_QUANTIZER, rounding=ROUND_HALF_UP)

    if payable_days == payable_working_days:
        net_salary = monthly_salary
    else:
        net_salary = (
            monthly_salary * Decimal(payable_days) / Decimal(payable_working_days)
        ).quantize(MONEY_QUANTIZER, rounding=ROUND_HALF_UP)

    return {
        "total_days_in_month": payable_working_days,
        "paid_timesheet_days": len(payable_timesheet_dates),
        "paid_weekend_days": 0,
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


def _pdf_escape(value):
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_salary_slip_pdf(slip):
    lines = [
        f"Salary Slip - {slip.get_month_display()} {slip.year}",
        f"Employee: {slip.user.get_full_name() or slip.user.username}",
        f"Employee ID: {slip.user.employee_id}",
        f"Generated On: {slip.generated_at:%d %b %Y %H:%M}",
        "",
        f"Monthly Salary: INR {slip.monthly_salary}",
        f"Per Day Salary: INR {slip.daily_salary}",
        f"Total Payable Working Days In Month: {slip.total_days_in_month}",
        f"Paid Approved Time Sheet Days: {slip.paid_timesheet_days}",
        f"Paid Public Holiday Days: {slip.paid_public_holiday_days}",
        f"Total Salary Counted Days: {slip.payable_days}",
        f"Unpaid Working Days: {slip.unpaid_days}",
        f"Net Salary: INR {slip.net_salary}",
    ]

    commands = []
    y_position = 700
    for index, line in enumerate(lines):
        safe_line = _pdf_escape(line)
        font_size = 18 if index == 0 else 12
        commands.append("BT")
        commands.append(f"/F1 {font_size} Tf")
        commands.append(f"50 {y_position} Td")
        commands.append(f"({safe_line}) Tj")
        commands.append("ET")
        y_position -= 28 if index == 0 else 20

    stream = "\n".join(commands).encode("latin-1", errors="replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]

    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_position = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))

    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_position}\n%%EOF".encode("ascii")
    )
    return bytes(pdf)
