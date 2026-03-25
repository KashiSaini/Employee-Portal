from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect

from accounts.access import is_reviewer


def approval_access_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user

        if not user.is_authenticated:
            return redirect("login")

        if is_reviewer(user):
            return view_func(request, *args, **kwargs)

        messages.error(request, "You are not allowed to access the approval center.")
        return redirect("dashboard_home")

    return _wrapped_view
