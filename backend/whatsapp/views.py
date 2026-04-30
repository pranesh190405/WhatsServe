import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http_status
from rest_framework.parsers import FormParser, MultiPartParser

from .tasks import process_incoming_message

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name="dispatch")
class WhatsAppWebhookView(APIView):
    """
    Twilio WhatsApp Webhook.
    Instantly returns 200 OK to Twilio and delegates processing
    to Celery background workers.
    """

    authentication_classes = []
    permission_classes = []
    parser_classes = [FormParser, MultiPartParser]

    def post(self, request):
        # Twilio sends form-encoded data.
        data = request.data or request.POST

        phone = data.get("From", "").strip()
        body = data.get("Body", "").strip()

        if not phone or not body:
            logger.warning("Webhook called with empty From=%r or Body=%r", phone, body)
            return Response({"status": "ignored"}, status=http_status.HTTP_200_OK)

        logger.info("Queuing incoming message from %s", phone)
        
        # Enqueue the Celery task
        process_incoming_message.delay(phone, body)

        # Return 200 immediately so Twilio doesn't time out
        return Response({"status": "queued"}, status=http_status.HTTP_200_OK)
