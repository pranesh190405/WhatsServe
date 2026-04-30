"""
Celery tasks for WhatsApp message processing.
The main entry point is process_incoming_message which routes
to the appropriate handler based on user role and conversation state.
"""
import logging
from celery import shared_task
from .models import ConversationState
from users.models import User
from jobs.models import Job, ConversationSession, ChatMessage
from .services import send_whatsapp_message, analyze_intent
from .handlers import (
    WELCOME_MESSAGE, BOOKING_ASK_CATEGORY, BOOKING_ASK_ISSUE,
    WARRANTY_ASK_SERIAL, TRACK_ASK_JOB_ID, INVALID_INPUT,
    handle_booking_category, handle_booking_issue,
    handle_warranty_check, handle_auto_book, handle_track_request,
    handle_customer_feedback, handle_customer_comment,
    handle_technician_message,
)

logger = logging.getLogger(__name__)

GREETING_WORDS = {"hi", "hello", "hey", "menu", "start", "restart", "home"}


@shared_task
def process_incoming_message(phone, body):
    """
    Main Celery task — routes incoming WhatsApp messages.
    1. Detect if sender is a technician → technician flow
    2. Check for active live chat → route to chat
    3. Check conversation state → resume flow
    4. If idle → parse intent via Gemini or fallback
    """
    logger.info("Processing message from %s: %s", phone, body)

    # Get or create user
    clean_phone = phone.replace("whatsapp:", "").replace("+", "")
    customer, _ = User.objects.get_or_create(
        phone_number=phone.replace("whatsapp:", ""),
        defaults={
            "username": clean_phone,
            "role": "customer",
        },
    )

    # ─── 1. TECHNICIAN CHECK ───────────────────────────────
    if customer.role == "technician":
        return handle_technician_message(phone, body, customer)

    # ─── 2. LIVE CHAT INTERCEPT ────────────────────────────
    active_chat = ConversationSession.objects.filter(
        customer=customer,
        status__in=["open", "assigned", "in_progress"]
    ).first()

    if active_chat:
        clean_body = body.strip().upper()
        if clean_body in ("EXIT", "HI", "HELLO", "HEY", "MENU", "START"):
            active_chat.status = "resolved"
            active_chat.save()
            ChatMessage.objects.create(
                conversation=active_chat,
                sender_type="system",
                content="Customer closed the conversation."
            )
            send_whatsapp_message(phone, "✅ You have left the chat. Have a great day!")
            send_whatsapp_message(phone, WELCOME_MESSAGE)
            return "chat_exited"

        ChatMessage.objects.create(
            conversation=active_chat,
            sender_type="customer",
            sender=customer,
            content=body
        )
        return "routed_to_chat"

    # ─── 3. STATE MACHINE ─────────────────────────────────
    conv_state, _ = ConversationState.objects.get_or_create(
        phone_number=phone,
        defaults={"state": "idle"},
    )

    state = conv_state.state

    if state == "awaiting_category":
        handle_booking_category(phone, body, conv_state)
        return "handled_category"
    elif state == "awaiting_issue":
        handle_booking_issue(phone, body, conv_state)
        return "handled_issue"
    elif state == "awaiting_serial":
        handle_warranty_check(phone, body, conv_state)
        return "handled_serial"
    elif state == "awaiting_auto_book":
        handle_auto_book(phone, body, conv_state)
        return "handled_auto_book"
    elif state == "awaiting_job_id":
        handle_track_request(phone, body, conv_state)
        return "handled_job_id"
    elif state == "customer_awaiting_feedback":
        handle_customer_feedback(phone, body, conv_state)
        return "handled_feedback"
    elif state == "customer_awaiting_comment":
        handle_customer_comment(phone, body, conv_state)
        return "handled_comment"

    # ─── 4. IDLE — CHECK GREETINGS ────────────────────────
    clean_body = body.strip().lower()
    if clean_body in GREETING_WORDS:
        conv_state.reset()
        send_whatsapp_message(phone, WELCOME_MESSAGE)
        return "welcome"

    # ─── 5. SMART INTENT DETECTION (Gemini / Fallback) ────
    intent_data = analyze_intent(body)
    intent = intent_data.get("intent", "UNKNOWN")
    logger.info("Detected intent: %s from body: %s", intent, body)

    if intent == "BOOK_SERVICE":
        cat = intent_data.get("category")
        issue = intent_data.get("issue")

        if cat and issue:
            # Both category and issue extracted — create job directly
            conv_state.context["category"] = cat
            conv_state.state = "awaiting_issue"
            conv_state.save()
            handle_booking_issue(phone, issue, conv_state)
        elif cat:
            # Category found but no issue yet
            conv_state.context["category"] = cat
            conv_state.state = "awaiting_issue"
            conv_state.save()
            send_whatsapp_message(
                phone,
                f"Got it — booking service for your *{cat}*. 👍\n\n{BOOKING_ASK_ISSUE}"
            )
        else:
            conv_state.state = "awaiting_category"
            conv_state.save()
            send_whatsapp_message(phone, BOOKING_ASK_CATEGORY)

    elif intent == "CHECK_WARRANTY":
        serial = intent_data.get("serial")
        if serial:
            conv_state.state = "awaiting_serial"
            conv_state.save()
            handle_warranty_check(phone, serial, conv_state)
        else:
            conv_state.state = "awaiting_serial"
            conv_state.save()
            send_whatsapp_message(phone, WARRANTY_ASK_SERIAL)

    elif intent == "TRACK_REQUEST":
        job_id = intent_data.get("job_id")
        if job_id:
            conv_state.state = "awaiting_job_id"
            conv_state.save()
            handle_track_request(phone, job_id, conv_state)
        else:
            conv_state.state = "awaiting_job_id"
            conv_state.save()
            send_whatsapp_message(phone, TRACK_ASK_JOB_ID)

    elif intent == "TALK_TO_AGENT":
        conv_state.reset()
        ConversationSession.objects.create(
            customer=customer,
            subject="General Inquiry (WhatsApp)",
            status="open"
        )
        reply = (
            "🧑‍💻 *Connecting you to an agent...*\n\n"
            "You are now connected to our support team. "
            "An agent will reply shortly.\n\n"
            "_(Type *EXIT* at any time to leave the chat)_"
        )
        send_whatsapp_message(phone, reply)

    else:
        # Unknown intent — show menu
        conv_state.reset()
        send_whatsapp_message(phone, INVALID_INPUT)

    return "processed"


@shared_task
def expire_old_assignments():
    """
    Periodic task: check for JobAssignments past their deadline.
    Runs every 5 minutes via Celery Beat.
    """
    from django.utils import timezone
    from jobs.models import JobAssignment

    expired = JobAssignment.objects.filter(
        status="pending",
        deadline__lt=timezone.now()
    )
    count = 0
    for assignment in expired:
        assignment.status = "expired"
        assignment.save()
        count += 1
        logger.info("Assignment %s expired.", assignment.id)
    return f"Expired {count} assignments."
