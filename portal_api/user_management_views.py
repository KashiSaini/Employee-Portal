from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User

from .serializers import PortalUserListSerializer, PortalUserRoleUpdateSerializer


def can_access_user_management(user):
    return user.is_superuser or getattr(user, "is_hr", False)


def can_assign_user_roles(user):
    return user.is_superuser


class UserManagementSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not can_access_user_management(request.user):
            return Response(
                {"detail": "Only superadmin and HR users can access the user management page."},
                status=403,
            )

        search_query = request.query_params.get("q", "").strip()
        users = User.objects.all().order_by("employee_id", "username")

        if search_query:
            users = users.filter(
                Q(employee_id__icontains=search_query)
                | Q(username__icontains=search_query)
                | Q(first_name__icontains=search_query)
                | Q(last_name__icontains=search_query)
                | Q(email__icontains=search_query)
            )

        return Response(
            {
                "search_query": search_query,
                "total_users": User.objects.count(),
                "filtered_count": users.count(),
                "can_assign_roles": can_assign_user_roles(request.user),
                "users": PortalUserListSerializer(users, many=True).data,
            }
        )


class UserRoleUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not can_assign_user_roles(request.user):
            return Response(
                {"detail": "Only superadmin users can update portal roles."},
                status=403,
            )

        serializer = PortalUserRoleUpdateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        target_user = serializer.save()
        display_name = target_user.get_full_name() or target_user.username

        return Response(
            {
                "message": f"Updated portal roles for {display_name}.",
                "user": PortalUserListSerializer(target_user).data,
            }
        )
