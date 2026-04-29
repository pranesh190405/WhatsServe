import os
import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http_status
from twilio.rest import Client
from twilio.request_validator import RequestValidator

from .models import ConversationState

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# Twilio Configuration — read from environment
# ──────────────────────────────────────────────────────────────
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "")  # e.g. whatsapp:+14155238886

# Build client lazily to avoid crash if credentials not yet set
_twilio_client = None


def _get_client():
    global _twilio_client
    if _twilio_client is None and TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
        _twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    return _twilio_client


# ──────────────────────────────────────────────────────────────
# Message Templates
# ──────────────────────────────────────────────────────────────
WELCOME_MESSAGE = (
    "👋 Welcome to *WhatsServe — Electronics Service Center*!\n\n"
    "How can we help you today?\n\n"
    "1️⃣ Book a Service\n"
    "2️⃣ Check Warranty\n"
    "3️⃣ Track Your Request\n\n"
    "Reply with *1*, *2*, or *3* to get started."
)

BOOKING_ASK_ISSUE = (
    "🔧 *Book a Service*\n\n"
    "Please describe the issue with your appliance.\n"
    "For example: _AC not cooling_, _TV screen blinking_, _Washing machine not draining_"
)

WARRANTY_ASK_SERIAL = (
    "🛡️ *Check Warranty*\n\n"
    "Please send us the *serial number* of your product.\n"
    "You can find it on the back or bottom of the appliance."
)

TRACK_ASK_JOB_ID = (
    "📋 *Track Your Request*\n\n"
    "Please send your *Job ID*.\n"
    "It looks like: `JOB-20260429-0001`"
)

INVALID_INPUT = (
    "❓ Sorry, I didn't understand that.\n\n"
    "Please reply with *1*, *2*, or *3* to choose an option:\n\n"
    "1️⃣ Book a Service\n"
    "2️⃣ Check Warranty\n"
    "3️⃣ Track Your Request"
)


# ──────────────────────────────────────────────────────────────
# Send a WhatsApp message via Twilio
# ──────────────────────────────────────────────────────────────
def send_whatsapp_message(to, text):
    """
    Send a WhatsApp message via Twilio.
    `to` should be just the phone number (e.g. '+919876543210').
    The function adds the 'whatsapp:' prefix automatically if missing.
    """
    client = _get_client()
    if not client:
        logger.warning(
            "Twilio credentials not configured — skipping WhatsApp send to %s", to
        )
        return None

    # Ensure whatsapp: prefix
    if not to.startswith("whatsapp:"):
        to = f"whatsapp:{to}"

    from_number = TWILIO_WHATSAPP_NUMBER
    if not from_number.startswith("whatsapp:"):
        from_number = f"whatsapp:{from_number}"

    try:
        message = client.messages.create(
            body=text,
            from_=from_number,
            to=to,
        )
        logger.info("WhatsApp message sent to %s — SID: %s", to, message.sid)
        return message.sid
    except Exception as e:
        logger.error("Failed to send WhatsApp message to %s: %s", to, e)
        return None


# ──────────────────────────────────────────────────────────────
# Conversation Flow Handlers
# ──────────────────────────────────────────────────────────────

def _handle_booking_issue(phone, text, conv_state):
    """User sent their issue description — create the job."""
    from jobs.models import Job
    from users.models import User

    # Get or create customer
    customer, _ = User.objects.get_or_create(
        phone_number=phone.replace("whatsapp:", ""),
        defaults={
            "username": phone.replace("whatsapp:", "").replace("+", ""),
            "role": "customer",
        },
    )

    # Create the job
    job = Job(
        title=f"Service Request — {text[:80]}",
        description=text,
        customer=customer,
    )
    job.save()

    conv_state.reset()

    reply = (
        f"✅ *Service booked successfully!*\n\n"
        f"📋 Job ID: `{job.job_id}`\n"
        f"📌 Status: Pending\n"
        f"📝 Issue: {text[:100]}\n\n"
        f"We'll assign a technician shortly and notify you via WhatsApp.\n\n"
        f"Reply *3* anytime to track your request."
    )
    send_whatsapp_message(phone, reply)


def _handle_warranty_check(phone, serial, conv_state):
    """User sent a serial number — look up warranty."""
    from jobs.models import Warranty

    conv_state.reset()

    try:
        warranty = Warranty.objects.get(serial_number__iexact=serial.strip())
        if warranty.is_valid:
            reply = (
                f"🛡️ *Warranty Status: ✅ Valid*\n\n"
                f"Product: {warranty.product_name}\n"
                f"Serial: `{warranty.serial_number}`\n"
                f"Purchased: {warranty.purchase_date.strftime('%d %b %Y')}\n"
                f"Expires: {warranty.expiry_date.strftime('%d %b %Y')}\n\n"
                f"Your product is covered under warranty."
            )
        else:
            reply = (
                f"🛡️ *Warranty Status: ❌ Expired*\n\n"
                f"Product: {warranty.product_name}\n"
                f"Serial: `{warranty.serial_number}`\n"
                f"Expired on: {warranty.expiry_date.strftime('%d %b %Y')}\n\n"
                f"Your warranty has expired. Service charges may apply."
            )
    except Warranty.DoesNotExist:
        reply = (
            f"🛡️ *Warranty Status: ⚠️ Not Found*\n\n"
            f"No warranty record found for serial number `{serial}`.\n\n"
            f"Please double-check the serial number or contact our store."
        )

    send_whatsapp_message(phone, reply)


def _handle_track_request(phone, job_id_text, conv_state):
    """User sent a Job ID — look up the job status."""
    from jobs.models import Job

    conv_state.reset()

    try:
        job = Job.objects.select_related("customer", "technician").get(
            job_id__iexact=job_id_text.strip()
        )
        technician_info = (
            f"Technician: {job.technician.first_name or job.technician.username}"
            if job.technician
            else "Technician: Not yet assigned"
        )
        reply = (
            f"📋 *Job Status: {job.get_status_display()}*\n\n"
            f"Job ID: `{job.job_id}`\n"
            f"Issue: {job.title}\n"
            f"{technician_info}\n"
            f"Created: {job.created_at.strftime('%d %b %Y, %I:%M %p')}\n"
            f"Last Updated: {job.updated_at.strftime('%d %b %Y, %I:%M %p')}"
        )
    except Job.DoesNotExist:
        reply = (
            f"📋 *Job Not Found*\n\n"
            f"No service request found for `{job_id_text}`.\n\n"
            f"Please check the Job ID and try again."
        )

    send_whatsapp_message(phone, reply)


# ──────────────────────────────────────────────────────────────
# Main Webhook View
# ──────────────────────────────────────────────────────────────

@method_decorator(csrf_exempt, name="dispatch")
class WhatsAppWebhookView(APIView):
    """
    Twilio WhatsApp Webhook.

    Twilio sends POST requests here when a message arrives.
    The payload contains form-encoded data with keys like:
        From, Body, To, MessageSid, etc.

    This view:
    1. Extracts the sender phone and message body.
    2. Looks up or creates a ConversationState for the user.
    3. Routes based on the user's current state (idle, awaiting_issue, etc.)
    4. Responds via Twilio API.
    """

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        # Twilio sends form-encoded data
        data = request.data if isinstance(request.data, dict) else request.POST

        phone = data.get("From", "").strip()
        body = data.get("Body", "").strip()

        if not phone or not body:
            return Response({"status": "ignored"}, status=http_status.HTTP_200_OK)

        logger.info("WhatsApp message from %s: %s", phone, body)

        # Get or create conversation state for this phone number
        conv_state, _ = ConversationState.objects.get_or_create(
            phone_number=phone,
            defaults={"state": "idle"},
        )

        # ── Route based on current conversation state ──────────

        if conv_state.state == "awaiting_issue":
            # User was asked for their issue description
            _handle_booking_issue(phone, body, conv_state)

        elif conv_state.state == "awaiting_serial":
            # User was asked for their serial number
            _handle_warranty_check(phone, body, conv_state)

        elif conv_state.state == "awaiting_job_id":
            # User was asked for their Job ID
            _handle_track_request(phone, body, conv_state)

        elif body == "1":
            # Book a Service — ask for issue description
            conv_state.state = "awaiting_issue"
            conv_state.save()
            send_whatsapp_message(phone, BOOKING_ASK_ISSUE)

        elif body == "2":
            # Check Warranty — ask for serial number
            conv_state.state = "awaiting_serial"
            conv_state.save()
            send_whatsapp_message(phone, WARRANTY_ASK_SERIAL)

        elif body == "3":
            # Track Request — ask for Job ID
            conv_state.state = "awaiting_job_id"
            conv_state.save()
            send_whatsapp_message(phone, TRACK_ASK_JOB_ID)

        elif body.lower() in ("hi", "hello", "hey", "menu", "start"):
            # Greeting — send welcome menu
            conv_state.reset()
            send_whatsapp_message(phone, WELCOME_MESSAGE)

        else:
            # Unknown input — send menu again
            conv_state.reset()
            send_whatsapp_message(phone, INVALID_INPUT)

        # Always return 200 to Twilio
        return Response({"status": "received"}, status=http_status.HTTP_200_OK)
