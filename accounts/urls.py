from django.urls import path
from .views import login_view, logout_view, manage_users_view

urlpatterns = [
    path("", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("users/", manage_users_view, name="manage_users"),
]
