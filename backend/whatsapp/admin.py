from django.contrib import admin
from .models import ConversationState


@admin.register(ConversationState)
class ConversationStateAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "state", "updated_at")
    list_filter = ("state",)
    search_fields = ("phone_number",)
    readonly_fields = ("updated_at",)
