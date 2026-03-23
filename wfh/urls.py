from django.urls import path
from .views import wfh_list, wfh_create, wfh_update, wfh_delete

urlpatterns = [
    path("wfh/", wfh_list, name="wfh_list"),
    path("wfh/apply/", wfh_create, name="wfh_create"),
    path("wfh/<int:pk>/edit/", wfh_update, name="wfh_update"),
    path("wfh/<int:pk>/delete/", wfh_delete, name="wfh_delete"),
]