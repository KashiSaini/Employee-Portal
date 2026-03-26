from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from accounts.access import filter_review_queryset, is_reviewer
from profiles.models import EmployeeProfile
from leave_management.models import LeaveRequest, ShortLeaveRequest
from timesheet.models import TimeSheetEntry
from claims.models import Claim
from wfh.models import WorkFromHomeRequest
from documents.models import SalarySlip, PolicyDocument, CompanyDocument

from .serializers import (
    EmployeeProfileSerializer,
    LeaveRequestSerializer,
    ShortLeaveRequestSerializer,
    TimeSheetEntrySerializer,
    ClaimSerializer,
    WorkFromHomeRequestSerializer,
    SalarySlipSerializer,
    PolicyDocumentSerializer,
    CompanyDocumentSerializer,
)

class StatusFilterMixin:
    def filter_status(self, qs):
        status = self.request.query_params.get("status")
        if status in {"pending", "approved", "rejected"}:
            qs = qs.filter(status=status)
        return qs




class EmployeeOwnedStatusMixin:
    def _check_edit_permission(self, obj):
        if is_reviewer(self.request.user):
            return

        if obj.user != self.request.user:
            raise PermissionDenied("You can only modify your own records.")

        if getattr(obj, "status", None) == "approved":
            raise PermissionDenied("Approved records cannot be modified.")

    def perform_update(self, serializer):
        obj = self.get_object()
        self._check_edit_permission(obj)

        if is_reviewer(self.request.user):
            serializer.save()
        else:
            serializer.save(user=self.request.user, status="pending")

    def perform_destroy(self, instance):
        self._check_edit_permission(instance)
        instance.delete()


class MyProfileViewSet(viewsets.GenericViewSet):
    serializer_class = EmployeeProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [FormParser, MultiPartParser]

    @action(detail=False, methods=["get", "patch"], url_path="me")
    def me(self, request):
        profile, _ = EmployeeProfile.objects.get_or_create(user=request.user)

        if request.method == "GET":
            serializer = self.get_serializer(profile)
            return Response(serializer.data)

        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ReviewableMixin:
    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        if not is_reviewer(request.user):
            raise PermissionDenied("You are not allowed to approve records.")
        obj = self.get_object()
        obj.status = "approved"
        obj.remarks = request.data.get("remarks", "")
        if hasattr(obj, "reviewed_at"):
            from django.utils import timezone
            obj.reviewed_at = timezone.now()
        obj.save()
        return Response({"status": "approved"})

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        if not is_reviewer(request.user):
            raise PermissionDenied("You are not allowed to reject records.")
        obj = self.get_object()
        obj.status = "rejected"
        obj.remarks = request.data.get("remarks", "")
        if hasattr(obj, "reviewed_at"):
            from django.utils import timezone
            obj.reviewed_at = timezone.now()
        obj.save()
        return Response({"status": "rejected"})


class LeaveRequestViewSet(StatusFilterMixin, EmployeeOwnedStatusMixin, ReviewableMixin, viewsets.ModelViewSet):
    serializer_class = LeaveRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = filter_review_queryset(LeaveRequest.objects.all().select_related("user"), self.request.user)
        return self.filter_status(qs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ShortLeaveRequestViewSet(StatusFilterMixin, EmployeeOwnedStatusMixin, ReviewableMixin, viewsets.ModelViewSet):
    serializer_class = ShortLeaveRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = filter_review_queryset(ShortLeaveRequest.objects.all().select_related("user"), self.request.user)
        return self.filter_status(qs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TimeSheetEntryViewSet(StatusFilterMixin, EmployeeOwnedStatusMixin, ReviewableMixin, viewsets.ModelViewSet):
    serializer_class = TimeSheetEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = filter_review_queryset(
            TimeSheetEntry.objects.all().select_related("user", "project"),
            self.request.user,
        )
        return self.filter_status(qs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ClaimViewSet(StatusFilterMixin, EmployeeOwnedStatusMixin, ReviewableMixin, viewsets.ModelViewSet):
    serializer_class = ClaimSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        qs = filter_review_queryset(Claim.objects.all().select_related("user"), self.request.user)
        return self.filter_status(qs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WorkFromHomeRequestViewSet(StatusFilterMixin, EmployeeOwnedStatusMixin, ReviewableMixin, viewsets.ModelViewSet):
    serializer_class = WorkFromHomeRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = filter_review_queryset(WorkFromHomeRequest.objects.all().select_related("user"), self.request.user)
        return self.filter_status(qs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SalarySlipViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SalarySlipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SalarySlip.objects.filter(user=self.request.user, is_visible=True).select_related("user")


class PolicyDocumentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PolicyDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PolicyDocument.objects.filter(is_active=True)


class CompanyDocumentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CompanyDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CompanyDocument.objects.filter(is_active=True)
