from django.urls import reverse
from rest_framework import serializers

from accounts.access import is_reviewer
from accounts.models import User
from claims.models import Claim
from documents.models import CompanyDocument, PolicyDocument, SalarySlip
from leave_management.models import LeaveRequest, ShortLeaveRequest
from profiles.models import EmployeeProfile
from projects.access import can_assign_project_members, get_assignable_team_members, is_user_assigned_to_project
from projects.models import ProjectAssignment
from timesheet.models import Project, TimeSheetEntry
from wfh.models import WorkFromHomeRequest


def value_from_attrs(attrs, instance, field_name):
    if field_name in attrs:
        return attrs[field_name]
    if instance is not None:
        return getattr(instance, field_name, None)
    return None


class EmployeeProfileSerializer(serializers.ModelSerializer):
    employee_id = serializers.CharField(source="user.employee_id", read_only=True)
    full_name = serializers.SerializerMethodField()
    first_name = serializers.CharField(source="user.first_name", required=False, allow_blank=True)
    last_name = serializers.CharField(source="user.last_name", required=False, allow_blank=True)
    email = serializers.EmailField(source="user.email", required=False, allow_blank=True)
    phone = serializers.CharField(source="user.phone", required=False, allow_blank=True)
    department = serializers.CharField(source="user.department", required=False, allow_blank=True)
    designation = serializers.CharField(source="user.designation", required=False, allow_blank=True)
    completion_percentage = serializers.IntegerField(read_only=True)

    class Meta:
        model = EmployeeProfile
        fields = [
            "employee_id",
            "full_name",
            "first_name",
            "last_name",
            "email",
            "phone",
            "department",
            "designation",
            "date_of_birth",
            "join_date",
            "gender",
            "blood_group",
            "emergency_contact_name",
            "emergency_contact_phone",
            "permanent_address",
            "current_address",
            "city",
            "state",
            "country",
            "postal_code",
            "father_name",
            "mother_name",
            "spouse_name",
            "highest_qualification",
            "institute_name",
            "passing_year",
            "skills",
            "bio",
            "completion_percentage",
        ]
        read_only_fields = ("employee_id", "full_name", "completion_percentage")

    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})

        for field, value in user_data.items():
            setattr(instance.user, field, value)
        instance.user.save()

        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()

        return instance


class ProjectMemberSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    team_display = serializers.CharField(source="get_team_display", read_only=True)

    class Meta:
        model = User
        fields = ["id", "employee_id", "username", "full_name", "team", "team_display"]

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class ProjectSerializer(serializers.ModelSerializer):
    team_manager = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_manager=True).order_by("employee_id", "username"),
        allow_null=True,
        required=False,
    )
    team_manager_name = serializers.SerializerMethodField()
    team_manager_employee_id = serializers.CharField(source="team_manager.employee_id", read_only=True)
    team_manager_team = serializers.CharField(source="team_manager.team", read_only=True)
    team_manager_team_display = serializers.CharField(source="team_manager.get_team_display", read_only=True)
    assigned_employees = serializers.SerializerMethodField()
    assigned_employee_ids = serializers.SerializerMethodField()
    assignable_employees = serializers.SerializerMethodField()
    can_assign_members = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "code",
            "description",
            "team_manager",
            "team_manager_name",
            "team_manager_employee_id",
            "team_manager_team",
            "team_manager_team_display",
            "assigned_employees",
            "assigned_employee_ids",
            "assignable_employees",
            "can_assign_members",
            "is_active",
        ]

    def get_team_manager_name(self, obj):
        if obj.team_manager is None:
            return ""
        return obj.team_manager.get_full_name() or obj.team_manager.username

    def get_assigned_employees(self, obj):
        employees = [assignment.employee for assignment in obj.employee_assignments.select_related("employee")]
        return ProjectMemberSerializer(employees, many=True).data

    def get_assigned_employee_ids(self, obj):
        return list(obj.employee_assignments.values_list("employee_id", flat=True))

    def get_assignable_employees(self, obj):
        request = self.context.get("request")
        if request is None or not can_assign_project_members(request.user, obj):
            return []

        employees = get_assignable_team_members(obj, request.user)
        return ProjectMemberSerializer(employees, many=True).data

    def get_can_assign_members(self, obj):
        request = self.context.get("request")
        if request is None:
            return False
        return can_assign_project_members(request.user, obj)

    def validate_team_manager(self, value):
        if value is not None and not value.has_team_scope:
            raise serializers.ValidationError("Selected user must be a manager with an assigned team.")
        return value

    def create(self, validated_data):
        project = super().create(validated_data)
        self._cleanup_assignments(project)
        return project

    def update(self, instance, validated_data):
        project = super().update(instance, validated_data)
        self._cleanup_assignments(project)
        return project

    def _cleanup_assignments(self, project):
        manager = project.team_manager
        if manager is None or not manager.team:
            project.employee_assignments.all().delete()
        else:
            valid_employee_ids = (
                User.objects.filter(team=manager.team)
                .exclude(pk=manager.pk)
                .values_list("pk", flat=True)
            )
            project.employee_assignments.exclude(employee_id__in=valid_employee_ids).delete()

        if hasattr(project, "_prefetched_objects_cache"):
            project._prefetched_objects_cache = {}


class ProjectAssignmentUpdateSerializer(serializers.Serializer):
    employee_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=True,
    )

    def validate_employee_ids(self, value):
        return list(dict.fromkeys(value))

    def validate(self, attrs):
        request = self.context["request"]
        project = self.context["project"]

        if not can_assign_project_members(request.user, project):
            raise serializers.ValidationError({"detail": "You are not allowed to assign employees for this project."})

        if project.team_manager is None or not project.team_manager.team:
            raise serializers.ValidationError({"detail": "Assign a team manager before assigning employees."})

        allowed_employee_ids = set(get_assignable_team_members(project, request.user).values_list("id", flat=True))
        invalid_employee_ids = [employee_id for employee_id in attrs["employee_ids"] if employee_id not in allowed_employee_ids]
        if invalid_employee_ids:
            raise serializers.ValidationError(
                {"employee_ids": "You can only assign employees from the team manager's team."}
            )

        return attrs

    def save(self, **kwargs):
        project = self.context["project"]
        request = self.context["request"]
        employee_ids = self.validated_data["employee_ids"]
        desired_employee_ids = set(employee_ids)
        existing_employee_ids = set(project.employee_assignments.values_list("employee_id", flat=True))

        if desired_employee_ids:
            project.employee_assignments.exclude(employee_id__in=desired_employee_ids).delete()
        else:
            project.employee_assignments.all().delete()

        new_assignments = [
            ProjectAssignment(project=project, employee_id=employee_id, assigned_by=request.user)
            for employee_id in employee_ids
            if employee_id not in existing_employee_ids
        ]
        if new_assignments:
            ProjectAssignment.objects.bulk_create(new_assignments)

        if hasattr(project, "_prefetched_objects_cache"):
            project._prefetched_objects_cache = {}

        return Project.objects.select_related("team_manager").prefetch_related("employee_assignments__employee").get(pk=project.pk)


class PortalUserListSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    team_display = serializers.CharField(source="get_team_display", read_only=True)
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "employee_id",
            "username",
            "full_name",
            "email",
            "team",
            "team_display",
            "is_superuser",
            "is_hr",
            "is_manager",
            "roles",
        ]

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username

    def get_roles(self, obj):
        roles = []

        if obj.is_superuser:
            roles.append("Superadmin")
        if obj.is_hr:
            roles.append("HR")
        if obj.is_manager:
            roles.append("Manager")
        if not roles:
            roles.append("Employee")
        if obj.team:
            roles.append(f"{obj.get_team_display()} Team")

        return roles


class PortalUserRoleUpdateSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    is_superuser = serializers.BooleanField(required=False, default=False)
    is_hr = serializers.BooleanField(required=False, default=False)
    is_manager = serializers.BooleanField(required=False, default=False)
    team = serializers.ChoiceField(choices=User.TEAM_CHOICES, required=False, allow_blank=True)

    def validate_user_id(self, value):
        try:
            return User.objects.get(pk=value)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError("User not found.") from exc

    def validate(self, attrs):
        request = self.context["request"]
        target_user = attrs["user_id"]
        make_superadmin = attrs.get("is_superuser", False)
        is_manager = attrs.get("is_manager", target_user.is_manager)
        team = attrs.get("team", target_user.team)

        if target_user == request.user and not make_superadmin:
            raise serializers.ValidationError(
                {"detail": "You cannot remove your own superadmin access from this page."}
            )

        if is_manager and not team:
            raise serializers.ValidationError({"team": "Team is required for managers."})

        return attrs

    def save(self, **kwargs):
        target_user = self.validated_data["user_id"]
        make_superadmin = self.validated_data.get("is_superuser", False)
        was_superadmin = target_user.is_superuser

        target_user.is_superuser = make_superadmin
        if make_superadmin:
            target_user.is_staff = True
        elif was_superadmin and target_user.is_staff:
            target_user.is_staff = False

        target_user.is_hr = self.validated_data.get("is_hr", False)
        target_user.is_manager = self.validated_data.get("is_manager", False)
        target_user.team = self.validated_data.get("team", target_user.team)
        target_user.save(update_fields=["is_superuser", "is_staff", "is_hr", "is_manager", "team"])
        return target_user


class LeaveRequestSerializer(serializers.ModelSerializer):
    total_days = serializers.IntegerField(read_only=True)
    leave_type_display = serializers.CharField(source="get_leave_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = LeaveRequest
        fields = "__all__"
        read_only_fields = ("user", "status", "remarks", "reviewed_at", "applied_at", "total_days")

    def validate(self, attrs):
        start_date = value_from_attrs(attrs, self.instance, "start_date")
        end_date = value_from_attrs(attrs, self.instance, "end_date")

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({"end_date": "End date cannot be earlier than start date."})

        return attrs


class ShortLeaveRequestSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = ShortLeaveRequest
        fields = "__all__"
        read_only_fields = ("user", "status", "remarks", "reviewed_at", "applied_at")

    def validate(self, attrs):
        start_time = value_from_attrs(attrs, self.instance, "start_time")
        end_time = value_from_attrs(attrs, self.instance, "end_time")

        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError({"end_time": "End time must be later than start time."})

        return attrs


class TimeSheetEntrySerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = TimeSheetEntry
        fields = "__all__"
        read_only_fields = ("user", "status", "remarks", "reviewed_at", "created_at", "updated_at", "project_name")

    def validate_project(self, value):
        request = self.context.get("request")

        if not value.is_active:
            raise serializers.ValidationError("Inactive projects cannot be used in the time sheet.")

        if request is None or is_reviewer(request.user):
            return value

        if not is_user_assigned_to_project(request.user, value):
            raise serializers.ValidationError("You can only log time against projects assigned to you.")

        return value

    def validate(self, attrs):
        hours = value_from_attrs(attrs, self.instance, "hours")

        if hours is not None and hours <= 0:
            raise serializers.ValidationError({"hours": "Hours must be greater than 0."})
        if hours is not None and hours > 24:
            raise serializers.ValidationError({"hours": "Hours cannot be more than 24."})

        return attrs


class ClaimSerializer(serializers.ModelSerializer):
    claim_type_display = serializers.CharField(source="get_claim_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    receipt_url = serializers.SerializerMethodField()

    class Meta:
        model = Claim
        fields = "__all__"
        read_only_fields = ("user", "status", "remarks", "reviewed_at", "submitted_at", "updated_at")
        sort_fields = ["updated_at"]

    def get_receipt_url(self, obj):
        return obj.receipt.url if obj.receipt else ""

    def validate(self, attrs):
        amount = value_from_attrs(attrs, self.instance, "amount")

        if amount is not None and amount <= 0:
            raise serializers.ValidationError({"amount": "Claim amount must be greater than 0."})

        return attrs


class WorkFromHomeRequestSerializer(serializers.ModelSerializer):
    total_days = serializers.IntegerField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = WorkFromHomeRequest
        fields = "__all__"
        read_only_fields = ("user", "status", "remarks", "reviewed_at", "applied_at", "updated_at", "total_days")

    def validate(self, attrs):
        start_date = value_from_attrs(attrs, self.instance, "start_date")
        end_date = value_from_attrs(attrs, self.instance, "end_date")

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({"end_date": "End date cannot be earlier than start date."})

        return attrs


class SalarySlipSerializer(serializers.ModelSerializer):
    month_display = serializers.CharField(source="get_month_display", read_only=True)
    detail_url = serializers.SerializerMethodField()

    class Meta:
        model = SalarySlip
        fields = [
            "id",
            "user",
            "month",
            "month_display",
            "year",
            "file",
            "total_days_in_month",
            "paid_timesheet_days",
            "paid_weekend_days",
            "paid_public_holiday_days",
            "payable_days",
            "unpaid_days",
            "monthly_salary",
            "daily_salary",
            "net_salary",
            "generated_at",
            "uploaded_at",
            "is_visible",
            "detail_url",
        ]

    def get_detail_url(self, obj):
        request = self.context.get("request")
        detail_url = reverse("salary_slip_detail", args=[obj.pk])
        return request.build_absolute_uri(detail_url) if request else detail_url


class PolicyDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PolicyDocument
        fields = "__all__"


class CompanyDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyDocument
        fields = "__all__"

