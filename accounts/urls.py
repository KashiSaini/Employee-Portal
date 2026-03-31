from django.urls import path
from . import views

urlpatterns = [
    # Existing auth URLs
    path("", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    
    # Password Reset URLs
    path("password-reset/", views.password_reset_request_view, name="password_reset_request"),
    path("password-reset/confirm/", views.password_reset_confirm_view, name="password_reset_confirm"),

    # User management URLs
    path("users/manage/", views.manage_users_view, name="manage_users"),
    path("users/create/", views.create_user_view, name="create_user"),
]