from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect


def approval_access_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user

        if not user.is_authenticated:
            return redirect("login")

        if user.is_staff or getattr(user, "is_hr", False) or getattr(user, "is_manager", False):
            return view_func(request, *args, **kwargs)

        messages.error(request, "You are not allowed to access the approval center.")
        return redirect("dashboard_home")

    return _wrapped_view