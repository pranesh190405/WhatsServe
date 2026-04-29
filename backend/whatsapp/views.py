import os
import logging
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Configuration — read from environment
# ──────────────────────────────────────────────
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "my_secure_verify_token")
WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/whatsapp")

WHATSAPP_API_URL = (
    f"https://graph.facebook.com/v21.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
)

# ──────────────────────────────────────────────
# Welcome menu sent to users
# ──────────────────────────────────────────────
WELCOME_MESSAGE = (
    "👋 Welcome to *WhatsServe*!\n\n"
    "How can we help you today?\n\n"
    "1️⃣ Book a Service\n"
    "2️⃣ Check Warranty\n"
    "3️⃣ Track Your Request\n\n"
    "Reply with *1*, *2*, or *3* to get started."
)


def send_whatsapp_message(to, text):
    """
    Send a text message via Meta WhatsApp Cloud API.
    """
    if not WHATSAPP_API_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        logger.warning("WhatsApp API credentials not configured — skipping send.")
        return None

    headers = {
        "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }

    try:
        resp = requests.post(WHATSAPP_API_URL, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logger.error(f"Failed to send WhatsApp message to {to}: {e}")
        return None


def extract_message_data(payload):
    """
    Parse the incoming Meta WhatsApp Cloud API webhook payload
    and extract the sender phone number and message text.
    Returns (phone_number, message_text) or (None, None).
    """
    try:
        entry = payload.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return None, None

        msg = messages[0]
        phone = msg.get("from", "")
        text = msg.get("text", {}).get("body", "").strip()

        return phone, text
    except (IndexError, KeyError, AttributeError):
        return None, None


class WhatsAppWebhookView(APIView):
    """
    Webhook for Meta WhatsApp Cloud API.

    GET  — Verification challenge from Meta.
    POST — Incoming messages. Parses the payload, sends a welcome menu
           or routes the user's choice (1/2/3) to n8n for processing.
    """

    def get(self, request):
        """Handle Meta webhook verification."""
        mode = request.query_params.get("hub.mode")
        token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")

        if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
            return Response(int(challenge), status=status.HTTP_200_OK)

        return Response(
            {"error": "Verification failed"}, status=status.HTTP_403_FORBIDDEN
        )

    def post(self, request):
        """
        Handle incoming WhatsApp messages.
        Routes the message to n8n or sends a welcome menu.
        """
        payload = request.data
        phone, text = extract_message_data(payload)

        if not phone:
            # Status update or non-message event — acknowledge silently
            return Response({"status": "ignored"}, status=status.HTTP_200_OK)

        logger.info(f"WhatsApp message from {phone}: {text}")

        # ── Route by user input ──────────────────────────────
        if text in ("1", "2", "3"):
            # Forward to n8n for workflow processing
            n8n_payload = {
                "phone": phone,
                "choice": text,
                "raw_message": text,
            }
            try:
                requests.post(N8N_WEBHOOK_URL, json=n8n_payload, timeout=10)
            except requests.RequestException as e:
                logger.error(f"Failed to forward to n8n: {e}")
                send_whatsapp_message(
                    phone,
                    "⚠️ Sorry, we're experiencing issues. Please try again later.",
                )
        else:
            # Any other message → send the welcome menu
            send_whatsapp_message(phone, WELCOME_MESSAGE)

        # Always return 200 to Meta
        return Response({"status": "received"}, status=status.HTTP_200_OK)
