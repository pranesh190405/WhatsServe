"""
URL configuration for WhatsServe project.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("feedback.urls")),
    path("api/v1/whatsapp/", include("whatsapp.urls")),
]
