from django.contrib import admin
from .models import Feedback

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "job", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("user__username", "comment")
    raw_id_fields = ("user", "job")
    readonly_fields = ("created_at", "updated_at")
