from django.urls import path
from .views import sign_off_view

urlpatterns = [
    path("sign-off/", sign_off_view, name="sign_off"),
]