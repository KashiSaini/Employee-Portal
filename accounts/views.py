from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

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


def _superadmin_only_response(request):
    if request.user.is_superuser:
        return None

    messages.error(request, "Only superadmin users can manage portal user roles.")
    return redirect("dashboard_home")


@login_required
def manage_users_view(request):
    blocked_response = _superadmin_only_response(request)
    if blocked_response:
        return blocked_response

    search_query = request.GET.get("q", "").strip()

    if request.method == "POST":
        search_query = request.POST.get("q", "").strip()
        target_user = get_object_or_404(User, pk=request.POST.get("user_id"))

        target_user.is_hr = request.POST.get("is_hr") == "on"
        target_user.is_manager = request.POST.get("is_manager") == "on"
        target_user.save(update_fields=["is_hr", "is_manager"])

        display_name = target_user.get_full_name() or target_user.username
        messages.success(request, f"Updated portal roles for {display_name}.")

        redirect_url = reverse("manage_users")
        if search_query:
            redirect_url = f"{redirect_url}?{urlencode({'q': search_query})}"
        return redirect(redirect_url)

    users = User.objects.all().order_by("employee_id", "username")

    if search_query:
        users = users.filter(
            Q(employee_id__icontains=search_query)
            | Q(username__icontains=search_query)
            | Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
            | Q(email__icontains=search_query)
        )

    context = {
        "users": users,
        "search_query": search_query,
        "total_users": User.objects.count(),
        "filtered_count": users.count(),
    }
    return render(request, "accounts/user_management.html", context)
