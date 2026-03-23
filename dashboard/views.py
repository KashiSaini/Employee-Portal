from datetime import date
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from claims.models import Claim
from leave_management.models import LeaveRequest, ShortLeaveRequest
from profiles.models import EmployeeProfile
from timesheet.models import TimeSheetEntry
from wfh.models import WorkFromHomeRequest

from attendance.models import DailyWorkLog


def safe_year_replace(original_date, year):
    try:
        return original_date.replace(year=year)
    except ValueError:
        # Handles 29 Feb for non-leap years
        return date(year, 2, 28)


def next_occurrence(original_date, today):
    upcoming = safe_year_replace(original_date, today.year)
    if upcoming < today:
        upcoming = safe_year_replace(original_date, today.year + 1)
    return upcoming


def get_upcoming_birthdays(limit=5):
    today = timezone.localdate()
    profiles = EmployeeProfile.objects.select_related("user").filter(date_of_birth__isnull=False)

    items = []
    for profile in profiles:
        upcoming = next_occurrence(profile.date_of_birth, today)
        items.append({
            "name": profile.user.get_full_name() or profile.user.username,
            "date": upcoming,
            "days_left": (upcoming - today).days,
        })

    items.sort(key=lambda item: item["date"])
    return items[:limit]


def get_upcoming_anniversaries(limit=5):
    today = timezone.localdate()
    profiles = EmployeeProfile.objects.select_related("user").filter(join_date__isnull=False)

    items = []
    for profile in profiles:
        upcoming = next_occurrence(profile.join_date, today)
        years = upcoming.year - profile.join_date.year

        items.append({
            "name": profile.user.get_full_name() or profile.user.username,
            "date": upcoming,
            "days_left": (upcoming - today).days,
            "years": years,
        })

    items.sort(key=lambda item: item["date"])
    return items[:limit]


def get_recent_activity(user, limit=6):
    activities = []

    for item in user.leave_requests.order_by("-applied_at")[:3]:
        activities.append({
            "title": "Leave request submitted",
            "meta": f"{item.get_leave_type_display()} • {item.start_date:%d %b %Y} to {item.end_date:%d %b %Y}",
            "status": item.get_status_display(),
            "time": item.applied_at,
        })

    for item in user.short_leave_requests.order_by("-applied_at")[:3]:
        activities.append({
            "title": "Short leave request submitted",
            "meta": f"{item.leave_date:%d %b %Y} • {item.start_time:%H:%M} to {item.end_time:%H:%M}",
            "status": item.get_status_display(),
            "time": item.applied_at,
        })

    for item in user.timesheet_entries.order_by("-created_at")[:3]:
        activities.append({
            "title": "Time sheet entry submitted",
            "meta": f"{item.project.name} • {item.work_date:%d %b %Y} • {item.hours} hours",
            "status": item.get_status_display(),
            "time": item.created_at,
        })

    for item in user.claims.order_by("-submitted_at")[:3]:
        activities.append({
            "title": "Claim submitted",
            "meta": f"{item.title} • ₹{item.amount} • {item.expense_date:%d %b %Y}",
            "status": item.get_status_display(),
            "time": item.submitted_at,
        })

    for item in user.wfh_requests.order_by("-applied_at")[:3]:
        activities.append({
            "title": "WFH request submitted",
            "meta": f"{item.start_date:%d %b %Y} to {item.end_date:%d %b %Y}",
            "status": item.get_status_display(),
            "time": item.applied_at,
        })

    activities.sort(key=lambda item: item["time"], reverse=True)
    return activities[:limit]


@login_required
def dashboard_home(request):
    today = timezone.localdate()
    profile, _ = EmployeeProfile.objects.get_or_create(user=request.user)

    birthdays = get_upcoming_birthdays()
    anniversaries = get_upcoming_anniversaries()
    recent_activity = get_recent_activity(request.user)
    today_work_log = DailyWorkLog.objects.filter(user=request.user, work_date=today).first()

    employee_counts = {
        "leave_total": request.user.leave_requests.count(),
        "short_leave_total": request.user.short_leave_requests.count(),
        "timesheet_total": request.user.timesheet_entries.count(),
        "claim_total": request.user.claims.count(),
        "wfh_total": request.user.wfh_requests.count(),
        "pending_total": (
            request.user.leave_requests.filter(status="pending").count()
            + request.user.short_leave_requests.filter(status="pending").count()
            + request.user.timesheet_entries.filter(status="pending").count()
            + request.user.claims.filter(status="pending").count()
            + request.user.wfh_requests.filter(status="pending").count()
        ),
    }

    can_review = (request.user.is_staff or getattr(request.user, "is_hr", False) or getattr(request.user, "is_manager", False))

    approval_counts = {
        "leave": 0,
        "short_leave": 0,
        "timesheet": 0,
        "claim": 0,
        "wfh": 0,
        "total": 0,
    }

    if can_review:
        approval_counts["leave"] = LeaveRequest.objects.filter(status="pending").count()
        approval_counts["short_leave"] = ShortLeaveRequest.objects.filter(status="pending").count()
        approval_counts["timesheet"] = TimeSheetEntry.objects.filter(status="pending").count()
        approval_counts["claim"] = Claim.objects.filter(status="pending").count()
        approval_counts["wfh"] = WorkFromHomeRequest.objects.filter(status="pending").count()
        approval_counts["total"] = sum(approval_counts.values())

    alerts = []

    if profile.completion_percentage < 100:
        alerts.append(f"Your profile is {profile.completion_percentage}% complete. Please update missing details.")

    if employee_counts["pending_total"] > 0:
        alerts.append(f"You currently have {employee_counts['pending_total']} pending item(s) waiting for review.")

    if can_review and approval_counts["total"] > 0:
        alerts.append(f"There are {approval_counts['total']} pending approvals in the approval center.")

    if not alerts:
        alerts.append("All caught up. No urgent actions right now.")

    context = {
        "today": today,
        "profile": profile,
        "birthdays": birthdays,
        "anniversaries": anniversaries,
        "recent_activity": recent_activity,
        "employee_counts": employee_counts,
        "alerts": alerts,
        "can_review": can_review,
        "approval_counts": approval_counts,
        "today_work_log": today_work_log,
        
    }
    return render(request, "dashboard/home.html", context)