from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import LoginForm, PortalUserCreationForm
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


def _can_access_user_management(user):
    return user.is_superuser or getattr(user, "is_hr", False)


def _can_assign_user_roles(user):
    return user.is_superuser


def _user_management_redirect(search_query=""):
    redirect_url = reverse("manage_users")
    if search_query:
        redirect_url = f"{redirect_url}?{urlencode({'q': search_query})}"
    return redirect_url


def _user_management_only_response(request):
    if _can_access_user_management(request.user):
        return None

    messages.error(request, "Only superadmin and HR users can access the user management page.")
    return redirect("dashboard_home")


@login_required
def manage_users_view(request):
    blocked_response = _user_management_only_response(request)
    if blocked_response:
        return blocked_response

    search_query = request.GET.get("q", "").strip()
    can_assign_roles = _can_assign_user_roles(request.user)

    if request.method == "POST":
        search_query = request.POST.get("q", "").strip()
        action = request.POST.get("action")

        if action == "update_roles":
            if not can_assign_roles:
                messages.error(request, "Only superadmin users can update portal roles.")
                return redirect(_user_management_redirect(search_query))

            target_user = get_object_or_404(User, pk=request.POST.get("user_id"))
            make_superadmin = request.POST.get("is_superuser") == "on"
            was_superadmin = target_user.is_superuser

            if target_user == request.user and not make_superadmin:
                messages.error(request, "You cannot remove your own superadmin access from this page.")
                return redirect(_user_management_redirect(search_query))

            target_user.is_superuser = make_superadmin
            if make_superadmin:
                target_user.is_staff = True
            elif was_superadmin and target_user.is_staff:
                target_user.is_staff = False

            target_user.is_hr = request.POST.get("is_hr") == "on"
            target_user.is_manager = request.POST.get("is_manager") == "on"
            target_user.save(update_fields=["is_superuser", "is_staff", "is_hr", "is_manager"])

            display_name = target_user.get_full_name() or target_user.username
            messages.success(request, f"Updated portal roles for {display_name}.")
            return redirect(_user_management_redirect(search_query))

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
        "can_assign_roles": can_assign_roles,
    }
    return render(request, "accounts/user_management.html", context)


@login_required
def create_user_view(request):
    blocked_response = _user_management_only_response(request)
    if blocked_response:
        return blocked_response

    can_assign_roles = _can_assign_user_roles(request.user)
    create_form = PortalUserCreationForm(
        request.POST or None,
        allow_role_assignment=can_assign_roles,
    )

    if request.method == "POST":
        if create_form.is_valid():
            new_user = create_form.save()
            display_name = new_user.get_full_name() or new_user.username
            messages.success(request, f"Created portal user {display_name}.")
            return redirect(_user_management_redirect(new_user.employee_id))

        messages.error(request, "Please correct the highlighted user creation errors.")

    context = {
        "create_form": create_form,
        "can_assign_roles": can_assign_roles,
    }
    return render(request, "accounts/user_create.html", context)
