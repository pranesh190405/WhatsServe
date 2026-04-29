from django.urls import path
from .views import CreateJobView, JobDetailView, JobListView, WarrantyCheckView

urlpatterns = [
    path("", JobListView.as_view(), name="job-list"),
    path("create-job/", CreateJobView.as_view(), name="create-job"),
    path("job/<str:job_id>/", JobDetailView.as_view(), name="job-detail"),
    path(
        "warranty/<str:serial_number>/",
        WarrantyCheckView.as_view(),
        name="warranty-check",
    ),
]
