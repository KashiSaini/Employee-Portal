def is_team_manager(user):
    return bool(getattr(user, "is_authenticated", False) and getattr(user, "is_manager", False) and getattr(user, "team", ""))


def is_reviewer(user):
    return bool(getattr(user, "is_staff", False) or getattr(user, "is_hr", False) or is_team_manager(user))


def can_access_user_management(user):
    return bool(getattr(user, "is_superuser", False) or getattr(user, "is_hr", False) or is_team_manager(user))


def can_create_users(user):
    return can_access_user_management(user)


def can_assign_user_roles(user):
    return bool(getattr(user, "is_superuser", False))


def filter_user_management_queryset(queryset, user):
    if getattr(user, "is_superuser", False) or getattr(user, "is_hr", False):
        return queryset
    if is_team_manager(user):
        return queryset.filter(team=user.team)
    return queryset.none()


def filter_review_queryset(queryset, user, related_user_field="user"):
    if getattr(user, "is_staff", False) or getattr(user, "is_hr", False):
        return queryset
    if is_team_manager(user):
        return queryset.filter(**{f"{related_user_field}__team": user.team})
    return queryset.filter(**{related_user_field: user})
