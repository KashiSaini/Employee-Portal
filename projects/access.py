from django.db.models import Q

from accounts.access import is_team_manager
from accounts.models import User
from timesheet.models import Project


def can_access_project_management(user):
    return bool(
        getattr(user, "is_authenticated", False)
        and (getattr(user, "is_superuser", False) or getattr(user, "is_hr", False) or is_team_manager(user))
    )


def can_manage_project_catalog(user):
    return bool(
        getattr(user, "is_authenticated", False)
        and (getattr(user, "is_superuser", False) or getattr(user, "is_hr", False))
    )


def can_assign_project_members(user, project=None):
    if not getattr(user, "is_authenticated", False):
        return False

    if can_manage_project_catalog(user):
        return True

    if not is_team_manager(user):
        return False

    if project is None:
        return True

    return project.team_manager_id == user.id


def filter_project_queryset(queryset, user):
    if can_manage_project_catalog(user):
        return queryset

    if is_team_manager(user):
        return queryset.filter(team_manager=user)

    return queryset.none()


def get_assignable_team_members(project, user):
    if not can_assign_project_members(user, project):
        return User.objects.none()

    manager = project.team_manager
    if manager is None or not manager.team:
        return User.objects.none()

    return (
        User.objects.filter(team=manager.team, is_active=True)
        .exclude(pk=manager.pk)
        .order_by("employee_id", "username")
    )


def get_available_projects_for_user(user):
    if not getattr(user, "is_authenticated", False):
        return Project.objects.none()

    return (
        Project.objects.filter(is_active=True)
        .filter(Q(team_manager=user) | Q(employee_assignments__employee=user))
        .distinct()
        .order_by("name", "code")
    )


def is_user_assigned_to_project(user, project):
    if not getattr(user, "is_authenticated", False):
        return False

    if project.team_manager_id == user.id:
        return True

    return project.employee_assignments.filter(employee=user).exists()
