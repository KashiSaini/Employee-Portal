from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.access import filter_review_queryset, is_reviewer
from attendance.models import DailyWorkLog
from dashboard.views import get_upcoming_birthdays, get_upcoming_anniversaries, get_recent_activity
from profiles.models import EmployeeProfile
from leave_management.models import LeaveRequest, ShortLeaveRequest
from timesheet.models import TimeSheetEntry
from claims.models import Claim
from wfh.models import WorkFromHomeRequest
from django.utils import timezone


def format_local_datetime(value, pattern):
    if not value:
        return ""

    if timezone.is_aware(value):
        value = timezone.localtime(value)

    return value.strftime(pattern)


class DashboardSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        profile, _ = EmployeeProfile.objects.get_or_create(user=request.user)

        birthdays = get_upcoming_birthdays()
        anniversaries = get_upcoming_anniversaries()
        recent_activity = get_recent_activity(request.user)

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

        can_review = is_reviewer(request.user)
        approval_counts = {
            "leave": 0,
            "short_leave": 0,
            "timesheet": 0,
            "claim": 0,
            "wfh": 0,
            "total": 0,
        }

        if can_review:
            approval_counts["leave"] = filter_review_queryset(
                LeaveRequest.objects.filter(status="pending"),
                request.user,
            ).count()
            approval_counts["short_leave"] = filter_review_queryset(
                ShortLeaveRequest.objects.filter(status="pending"),
                request.user,
            ).count()
            approval_counts["timesheet"] = filter_review_queryset(
                TimeSheetEntry.objects.filter(status="pending"),
                request.user,
            ).count()
            approval_counts["claim"] = filter_review_queryset(
                Claim.objects.filter(status="pending"),
                request.user,
            ).count()
            approval_counts["wfh"] = filter_review_queryset(
                WorkFromHomeRequest.objects.filter(status="pending"),
                request.user,
            ).count()
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

        today_work_log = DailyWorkLog.objects.filter(user=request.user, work_date=today).first()

        return Response({
            "profile": {
                "employee_id": request.user.employee_id,
                "full_name": request.user.get_full_name() or request.user.username,
                "email": request.user.email or "",
                "phone": request.user.phone or "",
                "department": request.user.department or "",
                "designation": request.user.designation or "",
                "team": request.user.team or "",
                "team_display": request.user.get_team_display() if request.user.team else "",
                "join_date": str(profile.join_date) if profile.join_date else "",
                "date_of_birth": str(profile.date_of_birth) if profile.date_of_birth else "",
                "completion_percentage": profile.completion_percentage,
                "work_mode": request.session.get("work_mode", ""),
            },
            "employee_counts": employee_counts,
            "alerts": alerts,
            "birthdays": birthdays,
            "anniversaries": anniversaries,
            "recent_activity": recent_activity,
            "can_review": can_review,
            "approval_counts": approval_counts,
            "today_work_log": {
                "first_login": format_local_datetime(today_work_log.first_login, "%H:%M") if today_work_log else "",
                "is_signed_off": today_work_log.is_signed_off if today_work_log else False,
                "total_work_hours": today_work_log.total_work_hours_display if today_work_log else "00:00",
            },
        })
