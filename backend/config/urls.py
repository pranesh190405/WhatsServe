"""
URL configuration for WhatsServe project.
"""

from django.contrib import admin
from django.urls import path, include

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/v1/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/v1/", include("feedback.urls")),
    path("api/v1/whatsapp/", include("whatsapp.urls")),
    path("api/v1/jobs/", include("jobs.urls")),
    path("api/v1/technicians/", include("users.urls")),
]
