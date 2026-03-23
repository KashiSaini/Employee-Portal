from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .forms import ProfileUpdateForm
from .models import EmployeeProfile


@login_required
def profile_detail(request):
    profile, created = EmployeeProfile.objects.get_or_create(user=request.user)
    return render(request, "profiles/profile_detail.html", {"profile": profile})


@login_required
def profile_update(request):
    profile, created = EmployeeProfile.objects.get_or_create(user=request.user)

    form = ProfileUpdateForm(request.POST or None, instance=profile)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile updated successfully.")
        return redirect("profile_detail")

    return render(request, "profiles/profile_update.html", {"form": form})