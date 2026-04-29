from rest_framework import serializers
from .models import User, TechnicianProfile


class TechnicianProfileSerializer(serializers.ModelSerializer):
    """Nested technician profile data."""

    skills_list = serializers.ListField(read_only=True)

    class Meta:
        model = TechnicianProfile
        fields = [
            "id",
            "skills",
            "skills_list",
            "availability",
            "average_rating",
            "total_jobs_completed",
            "total_jobs_rejected",
            "report_count",
            "extra_fields",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "average_rating",
            "total_jobs_completed",
            "total_jobs_rejected",
            "report_count",
            "created_at",
            "updated_at",
        ]


class TechnicianListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing technicians with their profile data.
    Used by the support team dashboard.
    """

    profile = TechnicianProfileSerializer(source="technician_profile", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "whatsapp_id",
            "profile",
        ]
        read_only_fields = fields


class TechnicianCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a new technician.
    Creates both User and TechnicianProfile in one step.
    """

    username = serializers.CharField(max_length=150)
    first_name = serializers.CharField(max_length=150, required=False, default="")
    last_name = serializers.CharField(max_length=150, required=False, default="")
    email = serializers.EmailField(required=False, default="")
    phone_number = serializers.CharField(max_length=20, required=False, default="")
    whatsapp_id = serializers.CharField(max_length=50, required=False, default="")
    password = serializers.CharField(
        max_length=128,
        required=False,
        default="",
        help_text="Leave empty to auto-generate",
    )

    # Profile fields
    skills = serializers.CharField(required=False, default="")
    availability = serializers.ChoiceField(
        choices=TechnicianProfile.AVAILABILITY_CHOICES,
        required=False,
        default="available",
    )
    notes = serializers.CharField(required=False, default="")
    extra_fields = serializers.JSONField(required=False, default=dict)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                f"User '{value}' already exists."
            )
        return value

    def create(self, validated_data):
        # Separate profile data
        profile_data = {
            "skills": validated_data.pop("skills", ""),
            "availability": validated_data.pop("availability", "available"),
            "notes": validated_data.pop("notes", ""),
            "extra_fields": validated_data.pop("extra_fields", {}),
        }

        password = validated_data.pop("password", "") or User.objects.make_random_password()

        user = User.objects.create_user(
            username=validated_data["username"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            email=validated_data.get("email", ""),
            phone_number=validated_data.get("phone_number", ""),
            whatsapp_id=validated_data.get("whatsapp_id", ""),
            password=password,
            role="technician",
        )

        TechnicianProfile.objects.create(user=user, **profile_data)

        return user


class TechnicianUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating a technician and their profile.
    """

    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(max_length=20, required=False)
    whatsapp_id = serializers.CharField(max_length=50, required=False)

    # Profile fields
    skills = serializers.CharField(required=False)
    availability = serializers.ChoiceField(
        choices=TechnicianProfile.AVAILABILITY_CHOICES, required=False
    )
    notes = serializers.CharField(required=False)
    extra_fields = serializers.JSONField(required=False)

    def update(self, user, validated_data):
        # Update user fields
        user_fields = ["first_name", "last_name", "email", "phone_number", "whatsapp_id"]
        for field in user_fields:
            if field in validated_data:
                setattr(user, field, validated_data[field])
        user.save()

        # Update profile fields
        profile, _ = TechnicianProfile.objects.get_or_create(user=user)
        profile_fields = ["skills", "availability", "notes", "extra_fields"]
        for field in profile_fields:
            if field in validated_data:
                setattr(profile, field, validated_data[field])
        profile.save()

        return user


class BulkTechnicianSerializer(serializers.Serializer):
    """
    Accepts a list of technicians for bulk import.
    """

    technicians = TechnicianCreateSerializer(many=True)

    def create(self, validated_data):
        created = []
        errors = []
        for i, tech_data in enumerate(validated_data["technicians"]):
            try:
                serializer = TechnicianCreateSerializer(data=tech_data)
                serializer.is_valid(raise_exception=True)
                user = serializer.save()
                created.append(user.username)
            except Exception as e:
                errors.append({"index": i, "data": tech_data, "error": str(e)})
        return {"created": created, "errors": errors}
