from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model with role-based access.
    Roles: Customer, Technician, Support (service team), Admin.
    """

    ROLE_CHOICES = (
        ("customer", "Customer"),
        ("technician", "Technician"),
        ("support", "Support Team"),
        ("admin", "Admin"),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="customer")
    phone_number = models.CharField(max_length=20, blank=True, default="")
    whatsapp_id = models.CharField(
        max_length=50,
        blank=True,
        default="",
        db_index=True,
        help_text="WhatsApp phone number ID for message routing",
    )

    class Meta:
        indexes = [
            models.Index(fields=["role"]),
        ]

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class TechnicianProfile(models.Model):
    """
    Extended profile for technician users.
    Supports custom extra columns via JSON field so that
    the support team can add arbitrary data fields.
    """

    AVAILABILITY_CHOICES = (
        ("available", "Available"),
        ("busy", "Busy"),
        ("offline", "Offline"),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="technician_profile",
        limit_choices_to={"role": "technician"},
    )
    skills = models.TextField(
        blank=True,
        default="",
        help_text="Comma-separated skills (e.g. AC Repair, Plumbing, Electrical)",
    )
    availability = models.CharField(
        max_length=20,
        choices=AVAILABILITY_CHOICES,
        default="available",
    )
    average_rating = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.00,
        help_text="Auto-calculated from feedback",
    )
    total_jobs_completed = models.PositiveIntegerField(default=0)
    total_jobs_rejected = models.PositiveIntegerField(default=0)
    report_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times reported by support team",
    )
    extra_fields = models.JSONField(
        default=dict,
        blank=True,
        help_text="Custom columns added by support team (key-value pairs)",
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Internal notes by support team",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-average_rating"]
        indexes = [
            models.Index(fields=["availability"]),
        ]

    @property
    def skills_list(self):
        """Return skills as a list."""
        if not self.skills:
            return []
        return [s.strip() for s in self.skills.split(",") if s.strip()]

    def __str__(self):
        return f"{self.user.username} — {self.get_availability_display()} ({self.average_rating}★)"
