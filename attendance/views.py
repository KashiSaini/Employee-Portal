from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from .models import DailyWorkLog


@login_required
def sign_off_view(request):
    today = timezone.localdate()
    now = timezone.now()

    work_log, _ = DailyWorkLog.objects.get_or_create(
        user=request.user,
        work_date=today,
        defaults={
            "first_login": now,
            "work_mode": request.session.get("work_mode", ""),
        }
    )

    was_already_signed_off = work_log.is_signed_off
    work_log.record_sign_off(now, request.session.get("work_mode", ""))

    if was_already_signed_off:
        messages.success(request, "Your latest sign off time has been updated for today.")
    else:
        messages.success(request, "Your workday has been signed off for today.")

    return render(request, "attendance/sign_off_summary.html", {"work_log": work_log})
