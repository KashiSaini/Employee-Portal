from django.urls import path
from .views import create_user_view, login_view, logout_view, manage_users_view

urlpatterns = [
    path("", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("users/", manage_users_view, name="manage_users"),
    path("users/create/", create_user_view, name="create_user"),
]
