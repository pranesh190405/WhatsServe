from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model with role-based access.
    Roles: Customer, Technician, Admin.
    """

    ROLE_CHOICES = (
        ("customer", "Customer"),
        ("technician", "Technician"),
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
