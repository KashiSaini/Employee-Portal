from django.urls import path
from .views import profile_detail, profile_update

urlpatterns = [
    path("profile/", profile_detail, name="profile_detail"),
    path("profile/edit/", profile_update, name="profile_update"),
]