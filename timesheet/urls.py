from django.urls import path
from .views import (
    timesheet_list,
    timesheet_create,
    timesheet_update,
    timesheet_delete,
)

urlpatterns = [
    path("timesheet/", timesheet_list, name="timesheet_list"),
    path("timesheet/add/", timesheet_create, name="timesheet_create"),
    path("timesheet/<int:pk>/edit/", timesheet_update, name="timesheet_update"),
    path("timesheet/<int:pk>/delete/", timesheet_delete, name="timesheet_delete"),
]