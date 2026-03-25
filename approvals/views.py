from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.access import filter_review_queryset
from claims.models import Claim
from leave_management.models import LeaveRequest, ShortLeaveRequest
from timesheet.models import TimeSheetEntry
from wfh.models import WorkFromHomeRequest
from django.urls import reverse
from .decorators import approval_access_required
from .forms import ReviewForm


def employee_label(user):
    return f"{user.get_full_name() or user.username} ({user.employee_id})"


def review_action_url(route_name, pk):
    return reverse(route_name, args=[pk])


def handle_review(request, obj, page_title, record_name, summary_fields, approve_url, reject_url):
    if obj.status != "pending":
        messages.error(request, "Only pending records can be reviewed from this page.")
        return redirect("approval_dashboard")

    form = ReviewForm(initial={"remarks": getattr(obj, "remarks", "")})

    context = {
        "page_title": page_title,
        "record_name": record_name,
        "summary_fields": summary_fields,
        "form": form,
        "approve_url": approve_url,
        "reject_url": reject_url,
    }
    return render(request, "approvals/review_form.html", context)


@approval_access_required
def approval_dashboard(request):
    leave_qs = filter_review_queryset(
        LeaveRequest.objects.filter(status="pending").select_related("user"),
        request.user,
    ).order_by("-applied_at")
    short_leave_qs = filter_review_queryset(
        ShortLeaveRequest.objects.filter(status="pending").select_related("user"),
        request.user,
    ).order_by("-applied_at")
    timesheet_qs = filter_review_queryset(
        TimeSheetEntry.objects.filter(status="pending").select_related("user", "project"),
        request.user,
    ).order_by("-created_at")
    claim_qs = filter_review_queryset(
        Claim.objects.filter(status="pending").select_related("user"),
        request.user,
    ).order_by("-submitted_at")
    wfh_qs = filter_review_queryset(
        WorkFromHomeRequest.objects.filter(status="pending").select_related("user"),
        request.user,
    ).order_by("-applied_at")

    pending_leave_count = leave_qs.count()
    pending_short_leave_count = short_leave_qs.count()
    pending_timesheet_count = timesheet_qs.count()
    pending_claim_count = claim_qs.count()
    pending_wfh_count = wfh_qs.count()

    total_pending = (
        pending_leave_count
        + pending_short_leave_count
        + pending_timesheet_count
        + pending_claim_count
        + pending_wfh_count
    )

    context = {
        "total_pending": total_pending,
        "pending_leave_count": pending_leave_count,
        "pending_short_leave_count": pending_short_leave_count,
        "pending_timesheet_count": pending_timesheet_count,
        "pending_claim_count": pending_claim_count,
        "pending_wfh_count": pending_wfh_count,
        "pending_leaves": leave_qs[:5],
        "pending_short_leaves": short_leave_qs[:5],
        "pending_timesheets": timesheet_qs[:5],
        "pending_claims": claim_qs[:5],
        "pending_wfh_requests": wfh_qs[:5],
    }
    return render(request, "approvals/approval_dashboard.html", context)


@approval_access_required
def review_leave(request, pk):
    leave = get_object_or_404(
        filter_review_queryset(LeaveRequest.objects.select_related("user"), request.user),
        pk=pk,
    )

    summary_fields = [
        ("Employee", employee_label(leave.user)),
        ("Leave Type", leave.get_leave_type_display()),
        ("Start Date", leave.start_date.strftime("%d %b %Y")),
        ("End Date", leave.end_date.strftime("%d %b %Y")),
        ("Total Days", str(leave.total_days)),
        ("Reason", leave.reason),
    ]

    return handle_review(
        request,
        leave,
        page_title="Review Leave Request",
        record_name="Leave request",
        summary_fields=summary_fields,
        approve_url=review_action_url("api-leave-approve", leave.pk),
        reject_url=review_action_url("api-leave-reject", leave.pk),
    )


@approval_access_required
def review_short_leave(request, pk):
    short_leave = get_object_or_404(
        filter_review_queryset(ShortLeaveRequest.objects.select_related("user"), request.user),
        pk=pk,
    )

    summary_fields = [
        ("Employee", employee_label(short_leave.user)),
        ("Leave Date", short_leave.leave_date.strftime("%d %b %Y")),
        ("Start Time", short_leave.start_time.strftime("%H:%M")),
        ("End Time", short_leave.end_time.strftime("%H:%M")),
        ("Reason", short_leave.reason),
    ]

    return handle_review(
        request,
        short_leave,
        page_title="Review Short Leave Request",
        record_name="Short leave request",
        summary_fields=summary_fields,
        approve_url=review_action_url("api-short-leave-approve", short_leave.pk),
        reject_url=review_action_url("api-short-leave-reject", short_leave.pk),
    )


@approval_access_required
def review_timesheet(request, pk):
    entry = get_object_or_404(
        filter_review_queryset(TimeSheetEntry.objects.select_related("user", "project"), request.user),
        pk=pk,
    )

    summary_fields = [
        ("Employee", employee_label(entry.user)),
        ("Project", entry.project.name),
        ("Work Date", entry.work_date.strftime("%d %b %Y")),
        ("Hours", str(entry.hours)),
        ("Description", entry.description),
    ]

    return handle_review(
        request,
        entry,
        page_title="Review Time Sheet Entry",
        record_name="Time sheet entry",
        summary_fields=summary_fields,
        approve_url=review_action_url("api-timesheet-approve", entry.pk),
        reject_url=review_action_url("api-timesheet-reject", entry.pk),
    )


@approval_access_required
def review_claim(request, pk):
    claim = get_object_or_404(
        filter_review_queryset(Claim.objects.select_related("user"), request.user),
        pk=pk,
    )

    summary_fields = [
        ("Employee", employee_label(claim.user)),
        ("Claim Type", claim.get_claim_type_display()),
        ("Title", claim.title),
        ("Amount", f"₹{claim.amount}"),
        ("Expense Date", claim.expense_date.strftime("%d %b %Y")),
        ("Description", claim.description),
    ]

    return handle_review(
        request,
        claim,
        page_title="Review Claim",
        record_name="Claim",
        summary_fields=summary_fields,
        approve_url=review_action_url("api-claims-approve", claim.pk),
        reject_url=review_action_url("api-claims-reject", claim.pk),
    )


@approval_access_required
def review_wfh(request, pk):
    wfh_request = get_object_or_404(
        filter_review_queryset(WorkFromHomeRequest.objects.select_related("user"), request.user),
        pk=pk,
    )

    summary_fields = [
        ("Employee", employee_label(wfh_request.user)),
        ("Start Date", wfh_request.start_date.strftime("%d %b %Y")),
        ("End Date", wfh_request.end_date.strftime("%d %b %Y")),
        ("Total Days", str(wfh_request.total_days)),
        ("Reason", wfh_request.reason),
        ("Work Plan", wfh_request.work_plan or "-"),
    ]

    return handle_review(
        request,
        wfh_request,
        page_title="Review Work From Home Request",
        record_name="WFH request",
        summary_fields=summary_fields,
        approve_url=review_action_url("api-wfh-approve", wfh_request.pk),
        reject_url=review_action_url("api-wfh-reject", wfh_request.pk),
    )
