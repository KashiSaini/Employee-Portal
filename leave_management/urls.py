from django.urls import path
from .views import leave_list, apply_leave, apply_short_leave

urlpatterns = [
    path("leave/", leave_list, name="leave_list"),
    path("leave/apply/", apply_leave, name="apply_leave"),
    path("short-leave/apply/", apply_short_leave, name="apply_short_leave"),
]