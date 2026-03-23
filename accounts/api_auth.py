from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

User = get_user_model()


class EmployeeTokenObtainPairSerializer(TokenObtainPairSerializer):
    employee_id = serializers.CharField(write_only=True)

    def validate(self, attrs):
        employee_id = attrs.pop("employee_id", None)
        password = attrs.get("password")

        try:
            user = User.objects.get(employee_id=employee_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid employee ID or password.")

        data = super().validate({
            self.username_field: getattr(user, self.username_field),
            "password": password,
        })
        data["employee_id"] = user.employee_id
        data["username"] = user.username
        return data


class EmployeeTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmployeeTokenObtainPairSerializer