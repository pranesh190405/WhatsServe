from django.contrib import admin
from .models import Job, Warranty


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("job_id", "title", "status", "customer", "technician", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("job_id", "title", "customer__username", "technician__username")
    readonly_fields = ("job_id", "created_at", "updated_at")
    raw_id_fields = ("customer", "technician")


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
