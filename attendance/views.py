from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import DailyWorkLog


@login_required
def sign_off_view(request):
    today = timezone.localdate()
    now = timezone.now()

    work_log, created = DailyWorkLog.objects.get_or_create(
        user=request.user,
        work_date=today,
        defaults={
            "first_login": now,
            "work_mode": request.session.get("work_mode", ""),
        }
    )

    if work_log.is_signed_off:
        messages.info(request, "You have already signed off for today.")
        return render(request, "attendance/sign_off_summary.html", {"work_log": work_log})

    work_log.sign_off_time = now
    total_seconds = int((work_log.sign_off_time - work_log.first_login).total_seconds())

    if total_seconds < 0:
        total_seconds = 0

    work_log.total_work_seconds = total_seconds
    work_log.is_signed_off = True

    if not work_log.work_mode:
        work_log.work_mode = request.session.get("work_mode", "")

    work_log.save()

    return render(request, "attendance/sign_off_summary.html", {"work_log": work_log})