from rest_framework import serializers
from profiles.models import EmployeeProfile
from leave_management.models import LeaveRequest, ShortLeaveRequest
from timesheet.models import TimeSheetEntry
from claims.models import Claim
from wfh.models import WorkFromHomeRequest
from documents.models import SalarySlip, PolicyDocument, CompanyDocument


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
    class Meta:
        model = SalarySlip
        fields = "__all__"



class PolicyDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PolicyDocument
        fields = "__all__"



class CompanyDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyDocument
        fields = "__all__"
