from django.urls import path
from .views import (
    TechnicianListView,
    TechnicianCreateView,
    TechnicianDetailView,
    TechnicianUpdateView,
    TechnicianDeleteView,
    TechnicianBulkImportView,
)

urlpatterns = [
    path("", TechnicianListView.as_view(), name="technician-list"),
    path("add/", TechnicianCreateView.as_view(), name="technician-add"),
    path("import/", TechnicianBulkImportView.as_view(), name="technician-import"),
    path("<int:pk>/", TechnicianDetailView.as_view(), name="technician-detail"),
    path("<int:pk>/update/", TechnicianUpdateView.as_view(), name="technician-update"),
    path("<int:pk>/delete/", TechnicianDeleteView.as_view(), name="technician-delete"),
]
