from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.access import can_access_user_management, can_assign_user_roles, filter_user_management_queryset
from accounts.models import User

from .serializers import PortalUserListSerializer, PortalUserRoleUpdateSerializer


class UserManagementSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not can_access_user_management(request.user):
            return Response(
                {
                    "detail": "Only superadmin, HR, and managers with an assigned team can access the user management page."
                },
                status=403,
            )

        search_query = request.query_params.get("q", "").strip()
        scoped_users = filter_user_management_queryset(User.objects.all(), request.user)
        users = scoped_users.order_by("employee_id", "username")

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
                "total_users": scoped_users.count(),
                "filtered_count": users.count(),
                "can_assign_roles": can_assign_user_roles(request.user),
                "team_choices": [{"value": value, "label": label} for value, label in User.TEAM_CHOICES],
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
