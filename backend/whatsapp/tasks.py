import re
import logging
from celery import shared_task
from .models import ConversationState
from users.models import User
from jobs.models import Job, ConversationSession, ChatMessage, Warranty
from .services import send_whatsapp_message, analyze_intent

logger = logging.getLogger(__name__)

# Templates
WELCOME_MESSAGE = (
    "👋 Welcome to *WhatsServe — Electronics Service Center*!\n\n"
    "How can we help you today?\n\n"
    "1️⃣ Book a Service\n"
    "2️⃣ Check Warranty\n"
    "3️⃣ Track Your Request\n"
    "4️⃣ Talk to Agent\n\n"
    "Reply with *1*, *2*, *3*, *4* or simply type your request!"
)

BOOKING_ASK_CATEGORY = (
    "🔧 *Book a Service*\n\n"
    "What type of appliance needs service?\n"
    "_(e.g., Air Conditioner, Refrigerator, Washing Machine, TV)_"
)

BOOKING_ASK_ISSUE = (
    "Great. Please describe the exact issue you're facing.\n"
    "_(e.g., Not cooling, Screen blinking, Making a loud noise)_"
)

WARRANTY_ASK_SERIAL = (
    "🛡️ *Check Warranty*\n\n"
    "Please send us the *serial number* of your product.\n"
    "You can find it on the back or bottom of the appliance."
)

TRACK_ASK_JOB_ID = (
    "📋 *Track Your Request*\n\n"
    "Please send your *Job ID* (or type *ALL* to see your recent requests).\n"
    "It looks like: `JOB-20260429-0001`"
)

INVALID_INPUT = (
    "❓ Sorry, I didn't understand that.\n\n"
    "Please reply with *1*, *2*, *3*, or *4* to choose an option:\n\n"
    "1️⃣ Book a Service\n"
    "2️⃣ Check Warranty\n"
    "3️⃣ Track Your Request\n"
    "4️⃣ Talk to Agent"
)


def _handle_booking_category(phone, text, conv_state):
    conv_state.context["category"] = text.strip()
    conv_state.state = "awaiting_issue"
    conv_state.save()
    send_whatsapp_message(phone, BOOKING_ASK_ISSUE)

def _handle_booking_issue(phone, text, conv_state):
    customer = User.objects.get(phone_number=phone.replace("whatsapp:", ""))
    category = conv_state.context.get("category", "General Appliance")

    job = Job.objects.create(
        title=f"{category[:40]} Repair",
        description=text,
        customer=customer,
    )
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
    cleaned_serial = re.sub(r'[^A-Za-z0-9]', '', serial).upper()

    try:
        warranty = Warranty.objects.get(serial_number__iexact=cleaned_serial)
        if warranty.is_valid:
            conv_state.state = "awaiting_auto_book"
            conv_state.context["product_name"] = warranty.product_name
            conv_state.save()
            
            reply = (
                f"🛡️ *Warranty Status: ✅ Valid*\n\n"
                f"Product: {warranty.product_name}\n"
                f"Serial: `{warranty.serial_number}`\n"
                f"Expires: {warranty.expiry_date.strftime('%d %b %Y')}\n\n"
                f"Would you like to book a *FREE service visit* for this product right now? Reply *YES* or *NO*."
            )
        else:
            conv_state.reset()
            reply = (
                f"🛡️ *Warranty Status: ❌ Expired*\n\n"
                f"Product: {warranty.product_name}\n"
                f"Serial: `{warranty.serial_number}`\n"
                f"Expired on: {warranty.expiry_date.strftime('%d %b %Y')}\n\n"
                f"Your warranty has expired. Service charges may apply. Reply *1* to book a service anyway."
            )
    except Warranty.DoesNotExist:
        conv_state.reset()
        reply = (
            f"🛡️ *Warranty Status: ⚠️ Not Found*\n\n"
            f"No warranty record found for serial number `{cleaned_serial}`.\n\n"
            f"Please double-check the serial number on your appliance."
        )

    send_whatsapp_message(phone, reply)

def _handle_auto_book(phone, text, conv_state):
    if text.strip().upper() == "YES":
        product_name = conv_state.context.get("product_name", "Appliance under Warranty")
        conv_state.context["category"] = product_name
        conv_state.state = "awaiting_issue"
        conv_state.save()
        send_whatsapp_message(phone, f"Booking service for your {product_name}.\n\n" + BOOKING_ASK_ISSUE)
    else:
        conv_state.reset()
        send_whatsapp_message(phone, "No problem! Reply *hi* anytime to return to the main menu.")

def _handle_track_request(phone, text, conv_state):
    conv_state.reset()
    clean_text = text.strip().upper()

    if clean_text == "ALL":
        jobs = Job.objects.filter(customer__phone_number=phone.replace("whatsapp:", "").replace("+", "")).order_by('-created_at')[:5]
        if not jobs:
            send_whatsapp_message(phone, "📋 No past or open service requests found for your number.")
            return
            
        reply = "📋 *Your Recent Requests:*\n\n"
        for j in jobs:
            reply += f"• `{j.job_id}` — {j.get_status_display()}\n"
        reply += "\nReply with a specific Job ID (e.g., `JOB-XXXXX`) for full details."
        send_whatsapp_message(phone, reply)
        return

    try:
        job = Job.objects.select_related("customer", "technician").get(
            job_id__iexact=clean_text
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
            f"No service request found for `{clean_text}`.\n\n"
            f"Please check the Job ID and try again, or type *ALL*."
        )

    send_whatsapp_message(phone, reply)


@shared_task
def process_incoming_message(phone, body):
    logger.info("Processing background message from %s: %s", phone, body)
    
    customer, _ = User.objects.get_or_create(
        phone_number=phone.replace("whatsapp:", ""),
        defaults={
            "username": phone.replace("whatsapp:", "").replace("+", ""),
            "role": "customer",
        },
    )

    # 1. Live Chat Intercept
    active_chat = ConversationSession.objects.filter(
        customer=customer,
        status__in=["open", "assigned", "in_progress"]
    ).first()

    if active_chat:
        if body.strip().upper() in ("EXIT", "HI", "HELLO", "HEY", "MENU", "START"):
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

    # 2. State Machine or GPT Logic
    conv_state, _ = ConversationState.objects.get_or_create(
        phone_number=phone,
        defaults={"state": "idle"},
    )

    # If in a specific flow, handle it
    if conv_state.state == "awaiting_category":
        _handle_booking_category(phone, body, conv_state)
        return "handled_category"
    elif conv_state.state == "awaiting_issue":
        _handle_booking_issue(phone, body, conv_state)
        return "handled_issue"
    elif conv_state.state == "awaiting_serial":
        _handle_warranty_check(phone, body, conv_state)
        return "handled_serial"
    elif conv_state.state == "awaiting_auto_book":
        _handle_auto_book(phone, body, conv_state)
        return "handled_auto_book"
    elif conv_state.state == "awaiting_job_id":
        _handle_track_request(phone, body, conv_state)
        return "handled_job_id"

    # 3. If idle, check for basic greetings or numbers first
    clean_body = body.strip().lower()
    if clean_body in ("hi", "hello", "hey", "menu", "start"):
        conv_state.reset()
        send_whatsapp_message(phone, WELCOME_MESSAGE)
        return "welcome"

    # 4. Use OpenAI GPT to parse intent
    intent_data = analyze_intent(body)
    intent = intent_data.get("intent", "UNKNOWN")

    if intent == "BOOK_SERVICE":
        cat = intent_data.get("category")
        if cat:
            conv_state.context["category"] = cat
            conv_state.state = "awaiting_issue"
            conv_state.save()
            send_whatsapp_message(phone, BOOKING_ASK_ISSUE)
        else:
            conv_state.state = "awaiting_category"
            conv_state.save()
            send_whatsapp_message(phone, BOOKING_ASK_CATEGORY)

    elif intent == "CHECK_WARRANTY":
        serial = intent_data.get("serial")
        if serial:
            conv_state.state = "awaiting_serial"
            conv_state.save()
            _handle_warranty_check(phone, serial, conv_state)
        else:
            conv_state.state = "awaiting_serial"
            conv_state.save()
            send_whatsapp_message(phone, WARRANTY_ASK_SERIAL)

    elif intent == "TRACK_REQUEST":
        job_id = intent_data.get("job_id")
        if job_id:
            conv_state.state = "awaiting_job_id"
            conv_state.save()
            _handle_track_request(phone, job_id, conv_state)
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
            "You are now connected to our support team. An agent will reply shortly.\n\n"
            "_(Type *EXIT* at any time to leave the chat)_"
        )
        send_whatsapp_message(phone, reply)

    else:
        # Fallback to invalid input message
        conv_state.reset()
        send_whatsapp_message(phone, INVALID_INPUT)

    return "processed_via_gpt"

@shared_task
def expire_old_assignments():
    """
    Cron job task to check for JobAssignments that passed their deadline.
    Runs every 5 minutes.
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
        # In a real app we might also notify support here
        logger.info(f"Assignment {assignment.id} expired.")
    return f"Expired {count} assignments."
