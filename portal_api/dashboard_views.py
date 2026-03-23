from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from attendance.models import DailyWorkLog
from dashboard.views import get_upcoming_birthdays, get_upcoming_anniversaries, get_recent_activity
from profiles.models import EmployeeProfile
from leave_management.models import LeaveRequest, ShortLeaveRequest
from timesheet.models import TimeSheetEntry
from claims.models import Claim
from wfh.models import WorkFromHomeRequest
from django.utils import timezone


def is_reviewer(user):
    return user.is_staff or getattr(user, "is_hr", False) or getattr(user, "is_manager", False)


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

        today_work_log = DailyWorkLog.objects.filter(user=request.user, work_date=today).first()

        return Response({
            "profile": {
                "employee_id": request.user.employee_id,
                "full_name": request.user.get_full_name() or request.user.username,
                "email": request.user.email or "",
                "phone": request.user.phone or "",
                "department": request.user.department or "",
                "designation": request.user.designation or "",
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
                "first_login": today_work_log.first_login.strftime("%H:%M") if today_work_log else "",
                "is_signed_off": today_work_log.is_signed_off if today_work_log else False,
                "total_work_hours": today_work_log.total_work_hours_display if today_work_log else "00:00",
            },
        })