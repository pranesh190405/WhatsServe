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


class JobAssignment(models.Model):
    """
    Tracks technician assignments to jobs.
    When a technician is assigned, they have 30 minutes to accept or reject.
    If rejected, support team is notified and reassigns another technician.
    Keeps full assignment history.
    """

    STATUS_CHOICES = (
        ("pending", "Pending"),      # Just assigned, awaiting response
        ("accepted", "Accepted"),    # Technician accepted
        ("rejected", "Rejected"),    # Technician rejected
        ("expired", "Expired"),      # 30 min timeout — no response
        ("reassigned", "Reassigned"),  # Support team reassigned to different tech
    )

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    technician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_assignments",
        limit_choices_to={"role": "technician"},
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assignments_made",
        limit_choices_to={"role__in": ["support", "admin"]},
        help_text="Support team member who made this assignment",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    rejection_reason = models.TextField(
        blank=True,
        default="",
        help_text="Reason provided by technician for rejecting",
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the technician accepted or rejected",
    )
    deadline = models.DateTimeField(
        null=True,
        blank=True,
        help_text="30 minutes from assignment — auto-expire if no response",
    )

    class Meta:
        ordering = ["-assigned_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["-assigned_at"]),
            models.Index(fields=["deadline"]),
        ]

    def save(self, *args, **kwargs):
        if not self.pk and not self.deadline:
            # Set 30-minute deadline on creation
            self.deadline = timezone.now() + timezone.timedelta(minutes=30)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        """Check if this assignment has expired (past deadline with no response)."""
        if self.status == "pending" and self.deadline:
            return timezone.now() > self.deadline
        return False

    def __str__(self):
        return f"{self.job.job_id} → {self.technician.username} ({self.get_status_display()})"


class TechnicianReport(models.Model):
    """
    Report filed by support team against a technician.
    Based on customer feedback or service issues.
    """

    SEVERITY_CHOICES = (
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    )

    technician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports_received",
        limit_choices_to={"role": "technician"},
    )
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="reports_filed",
        limit_choices_to={"role__in": ["support", "admin"]},
    )
    feedback = models.ForeignKey(
        "feedback.Feedback",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="technician_reports",
        help_text="The customer feedback that triggered this report",
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="technician_reports",
    )
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default="medium")
    reason = models.TextField(help_text="Reason for reporting the technician")
    action_taken = models.TextField(
        blank=True,
        default="",
        help_text="What action was taken (e.g. warning, suspension)",
    )
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["severity"]),
            models.Index(fields=["is_resolved"]),
        ]

    def __str__(self):
        return f"Report: {self.technician.username} — {self.get_severity_display()} ({self.created_at:%Y-%m-%d})"


class ConversationSession(models.Model):
    """
    Live chat session for 'Talk to Agent' feature.
    Customer initiates via WhatsApp, support team handles in dashboard.
    """

    STATUS_CHOICES = (
        ("open", "Open"),
        ("assigned", "Assigned to Agent"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
    )

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations",
        limit_choices_to={"role": "customer"},
    )
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="handled_conversations",
        limit_choices_to={"role__in": ["support", "admin"]},
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversations",
        help_text="Job this conversation is about (if applicable)",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    subject = models.CharField(max_length=255, blank=True, default="General Inquiry")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Chat #{self.pk}: {self.customer.username} — {self.get_status_display()}"


class ChatMessage(models.Model):
    """
    Individual message within a ConversationSession.
    """

    SENDER_CHOICES = (
        ("customer", "Customer"),
        ("agent", "Support Agent"),
        ("system", "System"),
    )

    conversation = models.ForeignKey(
        ConversationSession,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender_type = models.CharField(max_length=20, choices=SENDER_CHOICES)
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.sender_type}] {self.content[:50]}..."
