from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "phone_number", "is_staff")
    list_filter = ("role", "is_staff", "is_superuser", "is_active")
    search_fields = ("username", "email", "phone_number", "whatsapp_id")
    fieldsets = UserAdmin.fieldsets + (
        ("WhatsServe Info", {"fields": ("role", "phone_number", "whatsapp_id")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("WhatsServe Info", {"fields": ("role", "phone_number", "whatsapp_id")}),
    )
