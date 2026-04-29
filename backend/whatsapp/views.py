import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class WhatsAppWebhookView(APIView):
    """
    Webhook for Meta WhatsApp Cloud API.
    GET is used by Meta for verification.
    POST is used to receive incoming messages/events.
    """
    
    def get(self, request):
        mode = request.query_params.get("hub.mode")
        token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")

        verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "my_secure_verify_token")

        if mode == "subscribe" and token == verify_token:
            # Meta requires the challenge to be returned as an integer or string
            return Response(int(challenge), status=status.HTTP_200_OK)
        return Response({"error": "Invalid token"}, status=status.HTTP_403_FORBIDDEN)

    def post(self, request):
        payload = request.data
        
        # Here we would typically forward the payload to n8n via a webhook
        # For example: requests.post(N8N_WEBHOOK_URL, json=payload)
        
        print("Received WhatsApp webhook:", payload)
        
        # Return 200 OK to Meta to acknowledge receipt
        return Response({"status": "success"}, status=status.HTTP_200_OK)
