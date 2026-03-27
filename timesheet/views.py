from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import TimeSheetEntryForm
from .models import TimeSheetEntry


@login_required
def timesheet_list(request):
    entries = TimeSheetEntry.objects.filter(user=request.user).select_related("project").order_by("-work_date", "-created_at")
    return render(request, "timesheet/timesheet_list.html", {"entries": entries})


@login_required
def timesheet_create(request):
    form = TimeSheetEntryForm(user=request.user)
    return render(
        request,
        "timesheet/timesheet_form.html",
        {
            "form": form,
            "page_title": "Add Time Sheet Entry",
            "entry": None,
        },
    )


@login_required
def timesheet_update(request, pk):
    entry = get_object_or_404(TimeSheetEntry, pk=pk, user=request.user)

    if entry.status == "approved":
        messages.error(request, "Approved entries cannot be edited.")
        return redirect("timesheet_list")

    form = TimeSheetEntryForm(instance=entry, user=request.user)
    return render(
        request,
        "timesheet/timesheet_form.html",
        {
            "form": form,
            "page_title": "Edit Time Sheet Entry",
            "entry": entry,
        },
    )


@login_required
def timesheet_delete(request, pk):
    entry = get_object_or_404(TimeSheetEntry, pk=pk, user=request.user)

    if entry.status == "approved":
        messages.error(request, "Approved entries cannot be deleted.")
        return redirect("timesheet_list")

    return render(request, "timesheet/timesheet_confirm_delete.html", {"entry": entry})
