from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import LeaveRequestForm, ShortLeaveRequestForm
from .models import LeaveRequest, ShortLeaveRequest


@login_required
def leave_list(request):
    leaves = LeaveRequest.objects.filter(user=request.user).order_by("-applied_at")
    short_leaves = ShortLeaveRequest.objects.filter(user=request.user).order_by("-applied_at")

    context = {
        "leaves": leaves,
        "short_leaves": short_leaves,
    }
    return render(request, "leave_management/leave_list.html", context)


@login_required
def apply_leave(request):
    form = LeaveRequestForm()
    return render(request, "leave_management/apply_leave.html", {"form": form})


@login_required
def apply_short_leave(request):
    form = ShortLeaveRequestForm()
    return render(request, "leave_management/apply_short_leave.html", {"form": form})