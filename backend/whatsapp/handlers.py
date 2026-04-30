"""
Message handlers for customer and technician WhatsApp flows.
Called by tasks.py to keep the main task file clean.
"""
import re
import logging
from django.utils import timezone
from users.models import User, TechnicianProfile
from jobs.models import Job, JobAssignment, ConversationSession, ChatMessage, Warranty
from feedback.models import Feedback
from .services import send_whatsapp_message, extract_appliance_category, summarize_issue, generate_otp

logger = logging.getLogger(__name__)

# ── Message Templates ────────────────────────────────────────

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
    "Great! Please describe the issue you're facing.\n"
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
    "4️⃣ Talk to Agent\n\n"
    "Or just describe what you need!"
)


# ══════════════════════════════════════════════════════════════
# CUSTOMER HANDLERS
# ══════════════════════════════════════════════════════════════

def handle_booking_category(phone, text, conv_state):
    """User provided appliance category."""
    category = extract_appliance_category(text)
    conv_state.context["category"] = category
    conv_state.state = "awaiting_issue"
    conv_state.save()
    send_whatsapp_message(
        phone,
        f"Got it — *{category}*. 👍\n\n{BOOKING_ASK_ISSUE}"
    )


def handle_booking_issue(phone, text, conv_state):
    """User described the issue — create the job."""
    customer = User.objects.get(phone_number=phone.replace("whatsapp:", ""))
    category = conv_state.context.get("category", "General Appliance")
    issue_summary = summarize_issue(text, category)

    job = Job.objects.create(
        title=f"{category[:40]} Repair",
        description=issue_summary,
        customer=customer,
    )
    conv_state.reset()

    reply = (
        f"✅ *Service booked successfully!*\n\n"
        f"📋 Job ID: `{job.job_id}`\n"
        f"📌 Status: Pending\n"
        f"🔧 Appliance: {category}\n"
        f"📝 Issue: {issue_summary[:100]}\n\n"
        f"We'll assign a technician shortly and notify you via WhatsApp.\n\n"
        f"Reply *3* anytime to track your request."
    )
    send_whatsapp_message(phone, reply)


def handle_warranty_check(phone, serial, conv_state):
    """Check warranty by serial number."""
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
                f"Would you like to book a *FREE service visit*? Reply *YES* or *NO*."
            )
        else:
            conv_state.reset()
            reply = (
                f"🛡️ *Warranty Status: ❌ Expired*\n\n"
                f"Product: {warranty.product_name}\n"
                f"Serial: `{warranty.serial_number}`\n"
                f"Expired on: {warranty.expiry_date.strftime('%d %b %Y')}\n\n"
                f"Service charges may apply. Reply *1* to book a service anyway."
            )
    except Warranty.DoesNotExist:
        conv_state.reset()
        reply = (
            f"🛡️ *Warranty Status: ⚠️ Not Found*\n\n"
            f"No warranty record found for serial `{cleaned_serial}`.\n\n"
            f"Please double-check and try again."
        )

    send_whatsapp_message(phone, reply)


def handle_auto_book(phone, text, conv_state):
    """YES/NO after warranty check."""
    if text.strip().upper() == "YES":
        product_name = conv_state.context.get("product_name", "Appliance")
        conv_state.context["category"] = product_name
        conv_state.state = "awaiting_issue"
        conv_state.save()
        send_whatsapp_message(phone, f"Booking service for your *{product_name}*.\n\n{BOOKING_ASK_ISSUE}")
    else:
        conv_state.reset()
        send_whatsapp_message(phone, "No problem! Reply *hi* anytime to return to the main menu.")


def handle_track_request(phone, text, conv_state):
    """Track a job by ID or list all."""
    conv_state.reset()
    clean_text = text.strip().upper()

    if clean_text == "ALL":
        jobs = Job.objects.filter(
            customer__phone_number=phone.replace("whatsapp:", "").replace("+", "")
        ).order_by('-created_at')[:5]
        if not jobs:
            send_whatsapp_message(phone, "📋 No service requests found for your number.")
            return
        reply = "📋 *Your Recent Requests:*\n\n"
        for j in jobs:
            reply += f"• `{j.job_id}` — {j.get_status_display()}\n"
        reply += "\nReply with a Job ID for full details."
        send_whatsapp_message(phone, reply)
        return

    try:
        job = Job.objects.select_related("customer", "technician").get(job_id__iexact=clean_text)
        tech_info = (
            f"Technician: {job.technician.first_name or job.technician.username}"
            if job.technician else "Technician: Not yet assigned"
        )
        reply = (
            f"📋 *Job Status: {job.get_status_display()}*\n\n"
            f"Job ID: `{job.job_id}`\n"
            f"Issue: {job.title}\n"
            f"{tech_info}\n"
            f"Created: {job.created_at.strftime('%d %b %Y, %I:%M %p')}\n"
            f"Updated: {job.updated_at.strftime('%d %b %Y, %I:%M %p')}"
        )
    except Job.DoesNotExist:
        reply = (
            f"📋 *Job Not Found*\n\n"
            f"No request found for `{clean_text}`.\n"
            f"Check the Job ID or type *ALL*."
        )
    send_whatsapp_message(phone, reply)


def handle_customer_feedback(phone, text, conv_state):
    """Customer sends a 1-5 rating."""
    try:
        rating = int(text.strip())
        if rating < 1 or rating > 5:
            raise ValueError()
    except (ValueError, TypeError):
        send_whatsapp_message(phone, "Please reply with a number from *1* to *5* (1=Poor, 5=Excellent).")
        return

    job_id = conv_state.context.get("job_id")
    conv_state.context["rating"] = rating
    conv_state.state = "customer_awaiting_comment"
    conv_state.save()

    stars = "⭐" * rating
    send_whatsapp_message(
        phone,
        f"{stars} Thanks! Rating: {rating}/5\n\n"
        f"Any additional comments? _(Type *SKIP* to skip)_"
    )


def handle_customer_comment(phone, text, conv_state):
    """Customer sends optional comment after rating."""
    job_id = conv_state.context.get("job_id")
    rating = conv_state.context.get("rating", 3)
    comment = "" if text.strip().upper() == "SKIP" else text.strip()

    try:
        job = Job.objects.get(job_id=job_id)
        customer = User.objects.get(phone_number=phone.replace("whatsapp:", ""))
        Feedback.objects.create(
            user=customer,
            job=job,
            rating=rating,
            comment=comment,
        )
        # Update technician average rating
        if job.technician:
            _update_tech_rating(job.technician)
    except Exception as e:
        logger.error("Failed to save feedback: %s", e)

    conv_state.reset()
    send_whatsapp_message(phone, "🙏 Thank you for your feedback! Reply *hi* anytime for help.")


def _update_tech_rating(technician):
    """Recalculate technician's average rating from all feedback."""
    from django.db.models import Avg
    profile, _ = TechnicianProfile.objects.get_or_create(user=technician)
    avg = Feedback.objects.filter(
        job__technician=technician
    ).aggregate(avg=Avg("rating"))["avg"]
    if avg:
        profile.average_rating = round(avg, 2)
        profile.save()


# ══════════════════════════════════════════════════════════════
# TECHNICIAN HANDLERS
# ══════════════════════════════════════════════════════════════

def handle_technician_message(phone, body, tech_user):
    """Main router for technician WhatsApp messages."""
    from .models import ConversationState
    conv_state, _ = ConversationState.objects.get_or_create(
        phone_number=phone,
        defaults={"state": "idle"},
    )

    clean = body.strip().upper()

    # If tech is awaiting response to an assignment
    if conv_state.state == "tech_awaiting_response":
        return _handle_tech_accept_reject(phone, body, tech_user, conv_state)

    # If tech is awaiting OTP for job completion
    if conv_state.state == "tech_awaiting_otp":
        return _handle_tech_otp(phone, body, tech_user, conv_state)

    # If tech types DONE/COMPLETE — start completion flow
    if clean in ("DONE", "COMPLETE", "COMPLETED", "FINISH", "FINISHED"):
        return _handle_tech_start_completion(phone, tech_user, conv_state)

    # If tech types JOBS or MY JOBS — show assigned jobs
    if clean in ("JOBS", "MY JOBS", "MYJOBS"):
        return _handle_tech_list_jobs(phone, tech_user)

    # Default: show technician menu
    reply = (
        "🔧 *Technician Menu*\n\n"
        "• Type *JOBS* to see your assigned jobs\n"
        "• Type *DONE* to complete a job\n"
        "• Type *ACCEPT* or *REJECT* when you have a pending assignment\n\n"
        "If you have a pending assignment, reply *ACCEPT* or *REJECT <reason>*."
    )
    send_whatsapp_message(phone, reply)
    return "tech_menu_shown"


def _handle_tech_accept_reject(phone, body, tech_user, conv_state):
    """Technician accepts or rejects a pending assignment."""
    clean = body.strip().upper()
    assignment_id = conv_state.context.get("assignment_id")

    if not assignment_id:
        conv_state.reset()
        send_whatsapp_message(phone, "⚠️ No pending assignment found. Type *JOBS* to see your jobs.")
        return "no_assignment"

    try:
        assignment = JobAssignment.objects.select_related("job", "job__customer").get(
            pk=assignment_id, status="pending"
        )
    except JobAssignment.DoesNotExist:
        conv_state.reset()
        send_whatsapp_message(phone, "⚠️ This assignment is no longer pending. It may have expired.")
        return "assignment_gone"

    if assignment.is_expired:
        assignment.status = "expired"
        assignment.save()
        conv_state.reset()
        send_whatsapp_message(phone, "⏰ Sorry, this assignment has expired (30-minute timeout).")
        return "assignment_expired"

    if clean.startswith("ACCEPT"):
        assignment.status = "accepted"
        assignment.responded_at = timezone.now()
        assignment.save()
        conv_state.reset()

        job = assignment.job
        send_whatsapp_message(
            phone,
            f"✅ *Assignment Accepted!*\n\n"
            f"Job: `{job.job_id}`\n"
            f"Issue: {job.title}\n"
            f"Description: {job.description[:100]}\n\n"
            f"Please contact the customer and schedule a visit.\n"
            f"When done, type *DONE* to complete the job."
        )

        # Notify customer
        cust_phone = job.customer.phone_number or job.customer.whatsapp_id
        if cust_phone:
            tech_name = tech_user.first_name or tech_user.username
            send_whatsapp_message(
                cust_phone,
                f"🎉 *Good news!* Your technician *{tech_name}* has accepted your service request.\n\n"
                f"Job: `{job.job_id}`\n"
                f"They will contact you shortly to schedule the visit."
            )
        return "accepted"

    elif clean.startswith("REJECT"):
        reason = body.strip()[6:].strip() or "No reason provided"
        assignment.status = "rejected"
        assignment.rejection_reason = reason
        assignment.responded_at = timezone.now()
        assignment.save()

        # Update rejection count
        profile, _ = TechnicianProfile.objects.get_or_create(user=tech_user)
        profile.total_jobs_rejected += 1
        profile.save()

        # Reset job for reassignment
        job = assignment.job
        job.technician = None
        job.status = "pending"
        job.save()

        conv_state.reset()
        send_whatsapp_message(
            phone,
            f"❌ Assignment rejected.\nReason: {reason}\n\nThe job will be reassigned to another technician."
        )
        return "rejected"

    else:
        send_whatsapp_message(phone, "Please reply *ACCEPT* to accept or *REJECT <reason>* to reject.")
        return "awaiting_response"


def _handle_tech_start_completion(phone, tech_user, conv_state):
    """Tech wants to complete a job — find their active job and generate OTP."""
    active_jobs = Job.objects.filter(
        technician=tech_user,
        status="in_progress"
    ).order_by("-updated_at")

    if not active_jobs.exists():
        send_whatsapp_message(phone, "📋 You don't have any active jobs to complete.")
        return "no_active_jobs"

    if active_jobs.count() == 1:
        job = active_jobs.first()
    else:
        # Multiple active jobs — ask which one
        reply = "📋 *Which job are you completing?*\n\n"
        for j in active_jobs[:5]:
            reply += f"• `{j.job_id}` — {j.title}\n"
        reply += "\nReply with the Job ID."
        send_whatsapp_message(phone, reply)
        conv_state.state = "tech_awaiting_otp"
        conv_state.context["step"] = "select_job"
        conv_state.save()
        return "select_job"

    # Generate and send OTP
    _send_completion_otp(job, phone, conv_state)
    return "otp_sent"


def _send_completion_otp(job, tech_phone, conv_state):
    """Generate OTP, save to job, send to customer, prompt tech."""
    otp = generate_otp()
    job.completion_otp = otp
    job.save()

    # Send OTP to customer
    cust_phone = job.customer.phone_number or job.customer.whatsapp_id
    if cust_phone:
        send_whatsapp_message(
            cust_phone,
            f"🔐 *Job Completion Verification*\n\n"
            f"Your technician is completing job `{job.job_id}`.\n\n"
            f"Your OTP is: *{otp}*\n\n"
            f"Please share this code with the technician to confirm completion."
        )

    # Tell tech to ask for OTP
    conv_state.state = "tech_awaiting_otp"
    conv_state.context = {"job_id": job.job_id, "step": "verify"}
    conv_state.save()

    send_whatsapp_message(
        tech_phone,
        f"📋 Completing job `{job.job_id}`.\n\n"
        f"We've sent a *4-digit OTP* to the customer.\n"
        f"Please ask them for the code and type it here."
    )


def _handle_tech_otp(phone, body, tech_user, conv_state):
    """Technician enters OTP to complete a job."""
    step = conv_state.context.get("step", "verify")

    # If tech needs to select which job
    if step == "select_job":
        clean = body.strip().upper()
        try:
            job = Job.objects.get(job_id__iexact=clean, technician=tech_user, status="in_progress")
            _send_completion_otp(job, phone, conv_state)
            return "otp_sent"
        except Job.DoesNotExist:
            send_whatsapp_message(phone, "❌ Job not found or not assigned to you. Try again.")
            return "invalid_job"

    # Verify OTP
    job_id = conv_state.context.get("job_id")
    entered_otp = body.strip()

    try:
        job = Job.objects.get(job_id=job_id)
    except Job.DoesNotExist:
        conv_state.reset()
        send_whatsapp_message(phone, "⚠️ Job not found. Please try again with *DONE*.")
        return "job_not_found"

    if job.completion_otp and entered_otp == job.completion_otp:
        # OTP matches — complete the job
        job.status = "completed"
        job.completed_at = timezone.now()
        job.completion_otp = ""
        job.save()

        # Update tech stats
        profile, _ = TechnicianProfile.objects.get_or_create(user=tech_user)
        profile.total_jobs_completed += 1
        profile.save()

        conv_state.reset()
        send_whatsapp_message(
            phone,
            f"✅ *Job `{job.job_id}` completed successfully!*\n\n"
            f"Great work! 🎉"
        )

        # Notify customer and ask for feedback
        cust_phone = job.customer.phone_number or job.customer.whatsapp_id
        if cust_phone:
            send_whatsapp_message(
                cust_phone,
                f"✅ *Your service is complete!*\n\n"
                f"Job: `{job.job_id}` — {job.title}\n\n"
                f"How was your experience? Rate us:\n"
                f"Reply with a number from *1* (Poor) to *5* (Excellent)"
            )
            # Set customer's conv state to await feedback
            from .models import ConversationState
            cust_state, _ = ConversationState.objects.get_or_create(
                phone_number=cust_phone if not cust_phone.startswith("whatsapp:") else cust_phone,
                defaults={"state": "idle"},
            )
            # Also try with whatsapp: prefix
            if not cust_phone.startswith("whatsapp:"):
                cust_state2, _ = ConversationState.objects.get_or_create(
                    phone_number=f"whatsapp:{cust_phone}" if not cust_phone.startswith("+") else f"whatsapp:{cust_phone}",
                    defaults={"state": "idle"},
                )
                cust_state2.state = "customer_awaiting_feedback"
                cust_state2.context = {"job_id": job.job_id}
                cust_state2.save()
            cust_state.state = "customer_awaiting_feedback"
            cust_state.context = {"job_id": job.job_id}
            cust_state.save()

        return "completed"
    else:
        send_whatsapp_message(phone, "❌ Incorrect OTP. Please ask the customer again and try.")
        return "wrong_otp"


def _handle_tech_list_jobs(phone, tech_user):
    """Show technician their assigned jobs."""
    jobs = Job.objects.filter(
        technician=tech_user,
        status__in=["pending", "in_progress"]
    ).order_by("-updated_at")[:10]

    if not jobs:
        send_whatsapp_message(phone, "📋 You have no active jobs right now.")
        return "no_jobs"

    reply = "📋 *Your Active Jobs:*\n\n"
    for j in jobs:
        reply += f"• `{j.job_id}` — {j.title} ({j.get_status_display()})\n"
    reply += "\nType *DONE* when you complete a job."
    send_whatsapp_message(phone, reply)
    return "jobs_listed"
