from django.db import models
from django.conf import settings
from django.utils import timezone


def generate_job_id():
    """
    Generate a unique, human-readable job ID.
    Format: JOB-YYYYMMDD-XXXX (e.g. JOB-20260429-0001)
    Uses a daily counter that resets each day.
    """
    today = timezone.now().date()
    date_str = today.strftime("%Y%m%d")

    # Count existing jobs created today to get the next sequence number
    today_count = Job.objects.filter(created_at__date=today).count()
    seq = today_count + 1

    return f"JOB-{date_str}-{seq:04d}"


class Job(models.Model):
    """
    Service job created via WhatsApp or admin panel.
    Tracks service requests from creation to completion.
    """

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    )

    job_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        db_index=True,
        help_text="Auto-generated ID in format JOB-YYYYMMDD-XXXX",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_jobs",
    )
    technician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="technician_jobs",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["-created_at"]),
        ]

    def save(self, *args, **kwargs):
        if not self.job_id:
            self.job_id = generate_job_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.job_id}: {self.title}"


class Warranty(models.Model):
    """
    Product warranty records. Looked up by serial number
    to check warranty validity and expiry.
    """

    serial_number = models.CharField(max_length=100, unique=True, db_index=True)
    product_name = models.CharField(max_length=255)
    purchase_date = models.DateField()
    expiry_date = models.DateField()
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="warranties",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name_plural = "Warranties"
        ordering = ["-expiry_date"]

    @property
    def is_valid(self):
        return self.expiry_date >= timezone.now().date()

    @property
    def status_display(self):
        return "Valid" if self.is_valid else "Expired"

    def __str__(self):
        return f"{self.serial_number} — {self.product_name} ({self.status_display})"
