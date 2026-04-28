from django.contrib import admin
from .models import Job, Feedback


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "created_at")
    search_fields = ("title",)
    list_filter = ("created_at",)


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "job", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("user__username", "comment")
    raw_id_fields = ("user", "job")
    readonly_fields = ("created_at", "updated_at")
