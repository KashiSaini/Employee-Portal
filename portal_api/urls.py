from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.api_auth import EmployeeTokenObtainPairView

from .dashboard_views import DashboardSummaryAPIView
from .project_views import ProjectManagementSummaryAPIView, ProjectViewSet
from .session_views import SessionLoginAPIView, SessionLogoutAPIView, SignOffAPIView
from .user_management_views import UserManagementSummaryAPIView, UserRoleUpdateAPIView
from .views import (
    ClaimViewSet,
    CompanyDocumentViewSet,
    LeaveRequestViewSet,
    MyProfileViewSet,
    PolicyDocumentViewSet,
    SalarySlipViewSet,
    ShortLeaveRequestViewSet,
    TimeSheetEntryViewSet,
    WorkFromHomeRequestViewSet,
)

router = DefaultRouter()
router.register("profile", MyProfileViewSet, basename="api-profile")
router.register("leave-requests", LeaveRequestViewSet, basename="api-leave")
router.register("short-leave-requests", ShortLeaveRequestViewSet, basename="api-short-leave")
router.register("timesheet-entries", TimeSheetEntryViewSet, basename="api-timesheet")
router.register("claims", ClaimViewSet, basename="api-claims")
router.register("wfh-requests", WorkFromHomeRequestViewSet, basename="api-wfh")
router.register("salary-slips", SalarySlipViewSet, basename="api-salary-slips")
router.register("policies", PolicyDocumentViewSet, basename="api-policies")
router.register("documents", CompanyDocumentViewSet, basename="api-documents")
router.register("projects", ProjectViewSet, basename="api-project")

urlpatterns = [
    path("token/", EmployeeTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("session/login/", SessionLoginAPIView.as_view(), name="api-session-login"),
    path("session/logout/", SessionLogoutAPIView.as_view(), name="api-session-logout"),
    path("session/sign-off/", SignOffAPIView.as_view(), name="api-session-sign-off"),
    path("dashboard/summary/", DashboardSummaryAPIView.as_view(), name="api-dashboard-summary"),
    path("users/management/", UserManagementSummaryAPIView.as_view(), name="api-user-management-summary"),
    path("users/roles/update/", UserRoleUpdateAPIView.as_view(), name="api-user-role-update"),
    path("projects/management/", ProjectManagementSummaryAPIView.as_view(), name="api-project-management-summary"),
    path("", include(router.urls)),
]
