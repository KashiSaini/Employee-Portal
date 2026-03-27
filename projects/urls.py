from django.urls import path

from .views import project_management_view


urlpatterns = [
    path("projects/", project_management_view, name="project_management"),
]
