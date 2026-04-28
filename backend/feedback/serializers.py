from rest_framework import serializers
from .models import Feedback


class FeedbackSerializer(serializers.ModelSerializer):
    user_display = serializers.StringRelatedField(source="user", read_only=True)
    job_title = serializers.StringRelatedField(source="job", read_only=True)

    class Meta:
        model = Feedback
        fields = [
            "id",
            "user",
            "user_display",
            "job",
            "job_title",
            "rating",
            "comment",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
