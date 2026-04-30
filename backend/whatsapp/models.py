from django.db import models
from django.conf import settings


class ConversationState(models.Model):
    """
    Tracks per-user conversation state for multi-step WhatsApp flows.
    For example, when a user picks "1" (Book Service), we set their state
    to 'awaiting_issue' and wait for their next message to be the issue description.
    """

    STATE_CHOICES = (
        ("idle", "Idle — waiting for menu selection"),
        ("awaiting_category", "Awaiting appliance category (Book Service)"),
        ("awaiting_issue", "Awaiting issue description (Book Service)"),
        ("awaiting_serial", "Awaiting serial number (Check Warranty)"),
        ("awaiting_auto_book", "Awaiting YES/NO to auto-book after warranty"),
        ("awaiting_job_id", "Awaiting Job ID (Track Request)"),
        # Technician-specific states
        ("tech_awaiting_response", "Technician awaiting ACCEPT/REJECT"),
        ("tech_awaiting_otp", "Technician awaiting OTP to complete job"),
        # Customer post-service states
        ("customer_awaiting_feedback", "Customer awaiting rating feedback"),
        ("customer_awaiting_comment", "Customer awaiting feedback comment"),
    )

    phone_number = models.CharField(
        max_length=30,
        unique=True,
        db_index=True,
        help_text="WhatsApp phone number (e.g. +919876543210)",
    )
    state = models.CharField(max_length=40, choices=STATE_CHOICES, default="idle")
    context = models.JSONField(
        default=dict,
        blank=True,
        help_text="Temporary data for the current flow (e.g. partial form data)",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Conversation State"
        verbose_name_plural = "Conversation States"

    def reset(self):
        """Reset to idle state."""
        self.state = "idle"
        self.context = {}
        self.save()

    def __str__(self):
        return f"{self.phone_number} — {self.get_state_display()}"
