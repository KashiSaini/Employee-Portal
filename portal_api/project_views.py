from django.db.models import Q
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from projects.access import can_access_project_management, can_manage_project_catalog, filter_project_queryset
from timesheet.models import Project

from .serializers import ProjectAssignmentUpdateSerializer, ProjectMemberSerializer, ProjectSerializer


class ProjectManagementSummaryAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not can_access_project_management(request.user):
            return Response(
                {
                    "detail": "Only superadmin, HR, and team managers with an assigned team can access project management."
                },
                status=403,
            )

        search_query = request.query_params.get("q", "").strip()
        scoped_projects = filter_project_queryset(
            Project.objects.all().select_related("team_manager").prefetch_related("employee_assignments__employee"),
            request.user,
        ).distinct()
        projects = scoped_projects.order_by("code", "name")

        if search_query:
            projects = projects.filter(
                Q(name__icontains=search_query)
                | Q(code__icontains=search_query)
                | Q(description__icontains=search_query)
                | Q(team_manager__username__icontains=search_query)
                | Q(team_manager__employee_id__icontains=search_query)
                | Q(team_manager__first_name__icontains=search_query)
                | Q(team_manager__last_name__icontains=search_query)
                | Q(employee_assignments__employee__username__icontains=search_query)
                | Q(employee_assignments__employee__employee_id__icontains=search_query)
                | Q(employee_assignments__employee__first_name__icontains=search_query)
                | Q(employee_assignments__employee__last_name__icontains=search_query)
            ).distinct()

        can_manage_projects = can_manage_project_catalog(request.user)
        manager_choices = []
        if can_manage_projects:
            manager_queryset = User.objects.filter(is_manager=True).exclude(team="").order_by("team", "employee_id", "username")
            manager_choices = ProjectMemberSerializer(manager_queryset, many=True).data

        return Response(
            {
                "search_query": search_query,
                "total_projects": scoped_projects.count(),
                "filtered_count": projects.count(),
                "can_manage_projects": can_manage_projects,
                "manager_choices": manager_choices,
                "projects": ProjectSerializer(projects, many=True, context={"request": request}).data,
            }
        )


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Project.objects.all().select_related("team_manager").prefetch_related("employee_assignments__employee")
        return filter_project_queryset(queryset, self.request.user).distinct().order_by("code", "name")

    def create(self, request, *args, **kwargs):
        if not can_manage_project_catalog(request.user):
            raise PermissionDenied("Only superadmin and HR users can create projects.")
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not can_manage_project_catalog(request.user):
            raise PermissionDenied("Only superadmin and HR users can update projects.")
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if not can_manage_project_catalog(request.user):
            raise PermissionDenied("Only superadmin and HR users can update projects.")
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not can_manage_project_catalog(request.user):
            raise PermissionDenied("Only superadmin and HR users can delete projects.")
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"], url_path="assign-members")
    def assign_members(self, request, pk=None):
        project = self.get_object()
        serializer = ProjectAssignmentUpdateSerializer(
            data=request.data,
            context={"request": request, "project": project},
        )
        serializer.is_valid(raise_exception=True)
        project = serializer.save()

        return Response(
            {
                "message": "Project assignments updated successfully.",
                "project": self.get_serializer(project).data,
            }
        )

