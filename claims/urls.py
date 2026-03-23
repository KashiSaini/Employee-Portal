from django.urls import path
from .views import claim_list, claim_create, claim_update, claim_delete

urlpatterns = [
    path("claims/", claim_list, name="claim_list"),
    path("claims/add/", claim_create, name="claim_create"),
    path("claims/<int:pk>/edit/", claim_update, name="claim_update"),
    path("claims/<int:pk>/delete/", claim_delete, name="claim_delete"),
]