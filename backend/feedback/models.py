from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Job(models.Model):
    """
    Minimal stub for the Job model.
    Dev 1 owns the full Job model — this stub satisfies the FK constraint
    and will be replaced/migrated when the full model lands.
    """

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Feedback(models.Model):
    """
    Customer/user feedback linked to a specific job.
    """

    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="feedbacks",
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="feedbacks",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        choices=RATING_CHOICES,
    )
    comment = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["rating"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"Feedback #{self.pk} by {self.user} — {self.rating}★"
