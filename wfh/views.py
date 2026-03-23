from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import WorkFromHomeRequestForm
from .models import WorkFromHomeRequest


@login_required
def wfh_list(request):
    requests = WorkFromHomeRequest.objects.filter(user=request.user).order_by("-applied_at")
    pending_requests = requests.filter(status="pending").count()

    context = {
        "requests": requests,
        "pending_requests": pending_requests,
    }
    return render(request, "wfh/wfh_list.html", context)


@login_required
def wfh_create(request):
    form = WorkFromHomeRequestForm()
    return render(
        request,
        "wfh/wfh_form.html",
        {
            "form": form,
            "page_title": "Apply Work From Home",
            "wfh_request": None,
        },
    )


@login_required
def wfh_update(request, pk):
    wfh_request = get_object_or_404(WorkFromHomeRequest, pk=pk, user=request.user)

    if wfh_request.status == "approved":
        messages.error(request, "Approved WFH requests cannot be edited.")
        return redirect("wfh_list")

    form = WorkFromHomeRequestForm(instance=wfh_request)
    return render(
        request,
        "wfh/wfh_form.html",
        {
            "form": form,
            "page_title": "Edit Work From Home Request",
            "wfh_request": wfh_request,
        },
    )


@login_required
def wfh_delete(request, pk):
    wfh_request = get_object_or_404(WorkFromHomeRequest, pk=pk, user=request.user)

    if wfh_request.status == "approved":
        messages.error(request, "Approved WFH requests cannot be deleted.")
        return redirect("wfh_list")

    return render(request, "wfh/wfh_confirm_delete.html", {"wfh_request": wfh_request})