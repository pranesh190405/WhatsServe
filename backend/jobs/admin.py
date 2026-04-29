from django.contrib import admin
from .models import Job, Warranty, JobAssignment, TechnicianReport, ConversationSession, ChatMessage


class JobAssignmentInline(admin.TabularInline):
    model = JobAssignment
    extra = 0
    readonly_fields = ("assigned_at", "responded_at", "deadline")
    raw_id_fields = ("technician", "assigned_by")


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("job_id", "title", "status", "customer", "technician", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("job_id", "title", "customer__username", "technician__username")
    readonly_fields = ("job_id", "created_at", "updated_at")
    raw_id_fields = ("customer", "technician")
    inlines = [JobAssignmentInline]


@admin.register(Warranty)
class WarrantyAdmin(admin.ModelAdmin):
    list_display = (
        "serial_number",
        "product_name",
        "purchase_date",
        "expiry_date",
        "status_display",
        "customer",
    )
    list_filter = ("expiry_date",)
    search_fields = ("serial_number", "product_name", "customer__username")
    raw_id_fields = ("customer",)


@admin.register(JobAssignment)
class JobAssignmentAdmin(admin.ModelAdmin):
    list_display = ("job", "technician", "status", "assigned_by", "assigned_at", "deadline")
    list_filter = ("status",)
    search_fields = ("job__job_id", "technician__username")
    readonly_fields = ("assigned_at", "responded_at", "deadline")
    raw_id_fields = ("job", "technician", "assigned_by")


@admin.register(TechnicianReport)
class TechnicianReportAdmin(admin.ModelAdmin):
    list_display = ("technician", "severity", "reported_by", "is_resolved", "created_at")
    list_filter = ("severity", "is_resolved")
    search_fields = ("technician__username", "reason")
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("technician", "reported_by", "feedback", "job")


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(ConversationSession)
class ConversationSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "agent", "status", "subject", "created_at")
    list_filter = ("status",)
    search_fields = ("customer__username", "agent__username", "subject")
    readonly_fields = ("created_at", "updated_at", "closed_at")
    raw_id_fields = ("customer", "agent", "job")
    inlines = [ChatMessageInline]
