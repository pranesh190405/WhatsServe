from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, TechnicianProfile


class TechnicianProfileInline(admin.StackedInline):
    model = TechnicianProfile
    can_delete = False
    verbose_name_plural = "Technician Profile"
    fk_name = "user"
    extra = 0


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
    inlines = []

    def get_inlines(self, request, obj=None):
        """Show TechnicianProfile inline only for technician users."""
        if obj and obj.role == "technician":
            return [TechnicianProfileInline]
        return []


@admin.register(TechnicianProfile)
class TechnicianProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "availability", "average_rating", "total_jobs_completed", "report_count")
    list_filter = ("availability",)
    search_fields = ("user__username", "skills")
    readonly_fields = ("average_rating", "total_jobs_completed", "total_jobs_rejected", "report_count", "created_at", "updated_at")
    raw_id_fields = ("user",)
