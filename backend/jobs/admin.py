from django.contrib import admin
from .models import Job

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "status", "customer", "technician", "created_at")
    search_fields = ("title", "customer__username", "technician__username")
    list_filter = ("status", "created_at")
