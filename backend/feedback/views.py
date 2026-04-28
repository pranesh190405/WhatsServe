from rest_framework import viewsets
from .models import Feedback
from .serializers import FeedbackSerializer


class FeedbackViewSet(viewsets.ModelViewSet):
    """
    API endpoint for feedback CRUD.

    Supports:
      - GET    /api/v1/feedback/        → list all feedback
      - POST   /api/v1/feedback/        → create feedback (n8n webhook target)
      - GET    /api/v1/feedback/:id/    → retrieve single feedback
      - PUT    /api/v1/feedback/:id/    → full update
      - PATCH  /api/v1/feedback/:id/    → partial update
      - DELETE /api/v1/feedback/:id/    → delete
    """

    queryset = Feedback.objects.select_related("user", "job").all()
    serializer_class = FeedbackSerializer
