from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect

from .forms import LoginForm
from .models import User

from django.utils import timezone
from attendance.models import DailyWorkLog


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard_home")

    form = LoginForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        employee_id = form.cleaned_data["employee_id"]
        password = form.cleaned_data["password"]
        work_mode = form.cleaned_data["work_mode"]

        try:
            user_obj = User.objects.get(employee_id=employee_id)
        except User.DoesNotExist:
            messages.error(request, "Invalid employee ID or password.")
            return render(request, "accounts/login.html", {"form": form})

        user = authenticate(request, username=user_obj.username, password=password)

        if user is not None:
            login(request, user)
            request.session["work_mode"] = work_mode

            today = timezone.localdate()
            now = timezone.now()

            work_log, created = DailyWorkLog.objects.get_or_create(
                user=user,
                work_date=today,
                defaults={
                    "first_login": now,
                    "work_mode": work_mode,
                }
            )

            # Keep the very first login of the day unchanged
            # But if work mode is empty, fill it once
            if not work_log.work_mode:
                work_log.work_mode = work_mode
                work_log.save(update_fields=["work_mode"])

            return redirect("dashboard_home")

        messages.error(request, "Invalid employee ID or password.")

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("login")