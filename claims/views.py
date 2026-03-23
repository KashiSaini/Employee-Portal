from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ClaimForm
from .models import Claim


@login_required
def claim_list(request):
    claims = Claim.objects.filter(user=request.user).order_by("-submitted_at")
    pending_claims = claims.filter(status="pending").count()

    context = {
        "claims": claims,
        "pending_claims": pending_claims,
    }
    return render(request, "claims/claim_list.html", context)


@login_required
def claim_create(request):
    form = ClaimForm()
    return render(
        request,
        "claims/claim_form.html",
        {
            "form": form,
            "page_title": "Submit Claim",
            "claim": None,
        },
    )


@login_required
def claim_update(request, pk):
    claim = get_object_or_404(Claim, pk=pk, user=request.user)

    if claim.status == "approved":
        messages.error(request, "Approved claims cannot be edited.")
        return redirect("claim_list")

    form = ClaimForm(instance=claim)
    return render(
        request,
        "claims/claim_form.html",
        {
            "form": form,
            "page_title": "Edit Claim",
            "claim": claim,
        },
    )

@login_required
def claim_delete(request, pk):
    claim = get_object_or_404(Claim, pk=pk, user=request.user)

    if claim.status == "approved":
        messages.error(request, "Approved claims cannot be deleted.")
        return redirect("claim_list")

    return render(request, "claims/claim_confirm_delete.html", {"claim": claim})