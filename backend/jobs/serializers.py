from rest_framework import serializers
from .models import Job, Warranty


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
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


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
