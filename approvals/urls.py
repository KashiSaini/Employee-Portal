from django.urls import path
from .views import (
    approval_dashboard,
    review_leave,
    review_short_leave,
    review_timesheet,
    review_claim,
    review_wfh,
)

urlpatterns = [
    path("approvals/", approval_dashboard, name="approval_dashboard"),
    path("approvals/leave/<int:pk>/", review_leave, name="review_leave"),
    path("approvals/short-leave/<int:pk>/", review_short_leave, name="review_short_leave"),
    path("approvals/timesheet/<int:pk>/", review_timesheet, name="review_timesheet"),
    path("approvals/claim/<int:pk>/", review_claim, name="review_claim"),
    path("approvals/wfh/<int:pk>/", review_wfh, name="review_wfh"),
]