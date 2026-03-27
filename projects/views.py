from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .access import can_access_project_management


@login_required
def project_management_view(request):
    if not can_access_project_management(request.user):
        messages.error(
            request,
            "Only superadmin, HR, and team managers with an assigned team can access project management.",
        )
        return redirect("dashboard_home")

    return render(request, "projects/project_list.html")
