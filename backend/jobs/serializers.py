from rest_framework import serializers
from .models import Job, Warranty, JobAssignment, TechnicianReport, ConversationSession, ChatMessage


class JobCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a job via POST /create-job.
    Accepts customer_name and issue; auto-creates the job.
    """

    customer_name = serializers.CharField(
        write_only=True,
        help_text="Customer username or display name",
    )
    issue = serializers.CharField(
        source="description",
        help_text="Description of the service issue",
    )

    class Meta:
        model = Job
        fields = [
            "customer_name",
            "issue",
            "title",
        ]

    def create(self, validated_data):
        customer_name = validated_data.pop("customer_name")

        # Look up or create the customer user
        from users.models import User

        customer, _ = User.objects.get_or_create(
            username=customer_name,
            defaults={"role": "customer"},
        )

        validated_data["customer"] = customer
        return super().create(validated_data)


class JobDetailSerializer(serializers.ModelSerializer):
    """
    Full read-only serializer for job details.
    Used by GET /job/<job_id> and the dashboard listing.
    """

    customer_name = serializers.CharField(
        source="customer.username", read_only=True
    )
    technician_name = serializers.CharField(
        source="technician.username", read_only=True, default=None
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )
    active_assignment = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            "id",
            "job_id",
            "title",
            "description",
            "status",
            "status_display",
            "customer_name",
            "technician_name",
            "active_assignment",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_active_assignment(self, obj):
        """Get the latest pending/accepted assignment."""
        assignment = obj.assignments.filter(
            status__in=["pending", "accepted"]
        ).first()
        if assignment:
            return JobAssignmentSerializer(assignment).data
        return None


class WarrantySerializer(serializers.ModelSerializer):
    """
    Warranty status response for GET /warranty/<serial_number>.
    """

    status = serializers.CharField(source="status_display", read_only=True)
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = Warranty
        fields = [
            "serial_number",
            "product_name",
            "purchase_date",
            "expiry_date",
            "status",
            "is_valid",
        ]
        read_only_fields = fields


# ── Assignment Serializers ──────────────────────────────────

class JobAssignmentSerializer(serializers.ModelSerializer):
    """Read-only serializer for assignment records."""

    technician_name = serializers.CharField(
        source="technician.username", read_only=True
    )
    assigned_by_name = serializers.CharField(
        source="assigned_by.username", read_only=True, default=None
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )
    is_expired = serializers.BooleanField(read_only=True)
    job_id = serializers.CharField(source="job.job_id", read_only=True)

    class Meta:
        model = JobAssignment
        fields = [
            "id",
            "job_id",
            "technician_name",
            "assigned_by_name",
            "status",
            "status_display",
            "rejection_reason",
            "assigned_at",
            "responded_at",
            "deadline",
            "is_expired",
        ]
        read_only_fields = fields


class AssignTechnicianSerializer(serializers.Serializer):
    """
    Assign a technician to a job.
    """
    technician_id = serializers.IntegerField(help_text="User ID of the technician")

    def validate_technician_id(self, value):
        from users.models import User
        try:
            tech = User.objects.get(pk=value, role="technician", is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError("Technician not found or inactive.")
        return value


class RejectAssignmentSerializer(serializers.Serializer):
    """Technician rejects an assignment."""
    reason = serializers.CharField(
        required=False, default="", help_text="Optional rejection reason"
    )


# ── Report Serializers ──────────────────────────────────────

class TechnicianReportSerializer(serializers.ModelSerializer):
    """Serializer for technician reports."""

    technician_name = serializers.CharField(
        source="technician.username", read_only=True
    )
    reported_by_name = serializers.CharField(
        source="reported_by.username", read_only=True, default=None
    )
    severity_display = serializers.CharField(
        source="get_severity_display", read_only=True
    )

    class Meta:
        model = TechnicianReport
        fields = [
            "id",
            "technician",
            "technician_name",
            "reported_by",
            "reported_by_name",
            "feedback",
            "job",
            "severity",
            "severity_display",
            "reason",
            "action_taken",
            "is_resolved",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id", "technician_name", "reported_by_name",
            "severity_display", "created_at", "updated_at",
        ]


class CreateReportSerializer(serializers.Serializer):
    """Create a report against a technician."""

    technician_id = serializers.IntegerField()
    feedback_id = serializers.IntegerField(required=False, allow_null=True, default=None)
    job_id = serializers.CharField(required=False, allow_blank=True, default="")
    severity = serializers.ChoiceField(
        choices=TechnicianReport.SEVERITY_CHOICES, default="medium"
    )
    reason = serializers.CharField()
    action_taken = serializers.CharField(required=False, default="")


# ── Conversation Serializers ────────────────────────────────

class ChatMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(
        source="sender.username", read_only=True, default="System"
    )

    class Meta:
        model = ChatMessage
        fields = [
            "id",
            "sender_type",
            "sender_name",
            "content",
            "is_read",
            "created_at",
        ]
        read_only_fields = fields


class ConversationSessionSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(
        source="customer.username", read_only=True
    )
    agent_name = serializers.CharField(
        source="agent.username", read_only=True, default=None
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )
    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = ConversationSession
        fields = [
            "id",
            "customer_name",
            "agent_name",
            "job",
            "status",
            "status_display",
            "subject",
            "message_count",
            "last_message",
            "created_at",
            "updated_at",
            "closed_at",
        ]
        read_only_fields = fields

    def get_message_count(self, obj):
        return obj.messages.count()

    def get_last_message(self, obj):
        msg = obj.messages.last()
        if msg:
            return ChatMessageSerializer(msg).data
        return None


# ── Feedback Serializer (for support team view) ────────────

class FeedbackDetailSerializer(serializers.Serializer):
    """Full feedback view for the support team dashboard."""

    id = serializers.IntegerField()
    customer_name = serializers.CharField(source="user.username")
    job_id = serializers.CharField(source="job.job_id")
    job_title = serializers.CharField(source="job.title")
    technician_name = serializers.SerializerMethodField()
    rating = serializers.IntegerField()
    comment = serializers.CharField()
    created_at = serializers.DateTimeField()

    def get_technician_name(self, obj):
        if obj.job and obj.job.technician:
            return obj.job.technician.username
        return None
