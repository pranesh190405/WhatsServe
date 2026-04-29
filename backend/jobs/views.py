from django.utils import timezone
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response

from users.models import User, TechnicianProfile
from feedback.models import Feedback
from whatsapp.views import send_whatsapp_message
from .models import Job, Warranty, JobAssignment, TechnicianReport, ConversationSession, ChatMessage
from .serializers import (
    JobCreateSerializer,
    JobDetailSerializer,
    WarrantySerializer,
    JobAssignmentSerializer,
    AssignTechnicianSerializer,
    RejectAssignmentSerializer,
    TechnicianReportSerializer,
    CreateReportSerializer,
    ConversationSessionSerializer,
    ChatMessageSerializer,
    FeedbackDetailSerializer,
)


# ══════════════════════════════════════════════════════════════
# EXISTING JOB VIEWS
# ══════════════════════════════════════════════════════════════

class CreateJobView(generics.CreateAPIView):
    """
    POST /api/v1/jobs/create-job/
    Create a new service job.
    """

    serializer_class = JobCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = serializer.save()

        detail = JobDetailSerializer(job)
        return Response(
            {
                "message": f"Service job {job.job_id} created successfully.",
                "job": detail.data,
            },
            status=status.HTTP_201_CREATED,
        )


class JobDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/jobs/job/<job_id>/
    Retrieve job status and details by the human-readable job_id.
    """

    serializer_class = JobDetailSerializer
    lookup_field = "job_id"
    queryset = Job.objects.select_related("customer", "technician")


class JobListView(generics.ListAPIView):
    """
    GET /api/v1/jobs/
    List all jobs (for the dashboard).
    Supports query params: ?status=pending&search=keyword
    """

    serializer_class = JobDetailSerializer
    queryset = Job.objects.select_related("customer", "technician")

    def get_queryset(self):
        qs = super().get_queryset()
        status_filter = self.request.query_params.get("status")
        search = self.request.query_params.get("search")

        if status_filter:
            qs = qs.filter(status=status_filter)
        if search:
            qs = qs.filter(job_id__icontains=search) | qs.filter(
                title__icontains=search
            )
        return qs


class WarrantyCheckView(generics.RetrieveAPIView):
    """
    GET /api/v1/jobs/warranty/<serial_number>/
    Fetch warranty status (Valid / Expired + expiry date).
    """

    serializer_class = WarrantySerializer
    lookup_field = "serial_number"
    queryset = Warranty.objects.all()

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Warranty.DoesNotExist:
            return Response(
                {"error": "No warranty found for this serial number."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(instance)
        return Response(
            {
                "message": f"Warranty is {instance.status_display}.",
                "warranty": serializer.data,
            }
        )


# ══════════════════════════════════════════════════════════════
# JOB ASSIGNMENT VIEWS
# ══════════════════════════════════════════════════════════════

class AssignTechnicianView(APIView):
    """
    POST /api/v1/jobs/job/<job_id>/assign/
    Support team assigns a technician to a job.
    Sets a 30-minute deadline for the technician to respond.
    """

    def post(self, request, job_id):
        try:
            job = Job.objects.get(job_id=job_id)
        except Job.DoesNotExist:
            return Response(
                {"error": "Job not found."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = AssignTechnicianSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tech_id = serializer.validated_data["technician_id"]
        technician = User.objects.get(pk=tech_id)

        # Mark any existing pending assignments as reassigned
        job.assignments.filter(status="pending").update(status="reassigned")

        # Create new assignment with 30-minute deadline
        assignment = JobAssignment.objects.create(
            job=job,
            technician=technician,
            assigned_by=request.user if request.user.is_authenticated else None,
        )

        # Update the job's technician reference
        job.technician = technician
        job.status = "in_progress"
        job.save()

        # Notify technician via WhatsApp
        tech_phone = technician.phone_number or technician.whatsapp_id
        if tech_phone:
            message = (
                f"🔧 *New Job Assigned: {job.job_id}*\n\n"
                f"Title: {job.title}\n"
                f"Customer: {job.customer.username}\n\n"
                f"You have 30 minutes to accept or reject this assignment."
            )
            # In a real system, you'd add quick reply buttons. For now, text.
            send_whatsapp_message(tech_phone, message)

        detail = JobAssignmentSerializer(assignment)
        return Response(
            {
                "message": f"Technician '{technician.username}' assigned to {job.job_id}. "
                           f"Deadline: 30 minutes.",
                "assignment": detail.data,
            },
            status=status.HTTP_201_CREATED,
        )


class AcceptAssignmentView(APIView):
    """
    POST /api/v1/jobs/assignments/<id>/accept/
    Technician accepts a job assignment.
    """

    def post(self, request, pk):
        try:
            assignment = JobAssignment.objects.get(pk=pk, status="pending")
        except JobAssignment.DoesNotExist:
            return Response(
                {"error": "Assignment not found or already responded."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if assignment.is_expired:
            assignment.status = "expired"
            assignment.save()
            return Response(
                {"error": "Assignment has expired. Please contact support for reassignment."},
                status=status.HTTP_410_GONE,
            )

        assignment.status = "accepted"
        assignment.responded_at = timezone.now()
        assignment.save()

        return Response(
            {
                "message": f"Assignment for {assignment.job.job_id} accepted.",
                "assignment": JobAssignmentSerializer(assignment).data,
            }
        )


class RejectAssignmentView(APIView):
    """
    POST /api/v1/jobs/assignments/<id>/reject/
    Technician rejects a job assignment.
    Increments the rejection counter and notifies support.
    """

    def post(self, request, pk):
        try:
            assignment = JobAssignment.objects.get(pk=pk, status="pending")
        except JobAssignment.DoesNotExist:
            return Response(
                {"error": "Assignment not found or already responded."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = RejectAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        assignment.status = "rejected"
        assignment.rejection_reason = serializer.validated_data.get("reason", "")
        assignment.responded_at = timezone.now()
        assignment.save()

        # Update technician's rejection count
        profile, _ = TechnicianProfile.objects.get_or_create(user=assignment.technician)
        profile.total_jobs_rejected += 1
        profile.save()

        # Remove technician from job — needs reassignment
        job = assignment.job
        job.technician = None
        job.status = "pending"
        job.save()

        return Response(
            {
                "message": f"Assignment rejected. Support team has been notified for reassignment.",
                "assignment": JobAssignmentSerializer(assignment).data,
                "requires_reassignment": True,
            }
        )


class AssignmentListView(generics.ListAPIView):
    """
    GET /api/v1/jobs/assignments/
    List all assignments. Supports ?status=pending&job_id=JOB-xxx
    """

    serializer_class = JobAssignmentSerializer
    queryset = JobAssignment.objects.select_related("job", "technician", "assigned_by")

    def get_queryset(self):
        qs = super().get_queryset()
        status_filter = self.request.query_params.get("status")
        job_id = self.request.query_params.get("job_id")

        if status_filter:
            qs = qs.filter(status=status_filter)
        if job_id:
            qs = qs.filter(job__job_id=job_id)
        return qs


class PendingReassignmentsView(generics.ListAPIView):
    """
    GET /api/v1/jobs/assignments/pending-reassignment/
    Returns jobs that need reassignment:
    - Rejected assignments
    - Expired assignments (30 min timeout)
    """

    serializer_class = JobAssignmentSerializer

    def get_queryset(self):
        now = timezone.now()
        # Mark expired assignments
        JobAssignment.objects.filter(
            status="pending", deadline__lt=now
        ).update(status="expired")

        return JobAssignment.objects.filter(
            status__in=["rejected", "expired"]
        ).select_related("job", "technician", "assigned_by").order_by("-assigned_at")


# ══════════════════════════════════════════════════════════════
# FEEDBACK VIEWS (for Support Team)
# ══════════════════════════════════════════════════════════════

class FeedbackListView(generics.ListAPIView):
    """
    GET /api/v1/jobs/feedback/
    Support team views all customer feedback.
    Supports: ?rating=1&technician=username
    """

    serializer_class = FeedbackDetailSerializer
    queryset = Feedback.objects.select_related("user", "job", "job__technician").order_by("-created_at")

    def get_queryset(self):
        qs = super().get_queryset()
        rating = self.request.query_params.get("rating")
        technician = self.request.query_params.get("technician")

        if rating:
            qs = qs.filter(rating=rating)
        if technician:
            qs = qs.filter(job__technician__username__icontains=technician)
        return qs


# ══════════════════════════════════════════════════════════════
# TECHNICIAN REPORT VIEWS
# ══════════════════════════════════════════════════════════════

class ReportListView(generics.ListAPIView):
    """
    GET /api/v1/jobs/reports/
    List all technician reports. Supports ?severity=high&resolved=false
    """

    serializer_class = TechnicianReportSerializer
    queryset = TechnicianReport.objects.select_related(
        "technician", "reported_by", "feedback", "job"
    )

    def get_queryset(self):
        qs = super().get_queryset()
        severity = self.request.query_params.get("severity")
        resolved = self.request.query_params.get("resolved")
        technician = self.request.query_params.get("technician")

        if severity:
            qs = qs.filter(severity=severity)
        if resolved is not None:
            qs = qs.filter(is_resolved=resolved.lower() == "true")
        if technician:
            qs = qs.filter(technician__username__icontains=technician)
        return qs


class CreateReportView(APIView):
    """
    POST /api/v1/jobs/reports/create/
    Support team reports a technician.
    """

    def post(self, request):
        serializer = CreateReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            technician = User.objects.get(pk=data["technician_id"], role="technician")
        except User.DoesNotExist:
            return Response(
                {"error": "Technician not found."}, status=status.HTTP_404_NOT_FOUND
            )

        feedback_obj = None
        if data.get("feedback_id"):
            try:
                feedback_obj = Feedback.objects.get(pk=data["feedback_id"])
            except Feedback.DoesNotExist:
                pass

        job_obj = None
        if data.get("job_id"):
            try:
                job_obj = Job.objects.get(job_id=data["job_id"])
            except Job.DoesNotExist:
                pass

        report = TechnicianReport.objects.create(
            technician=technician,
            reported_by=request.user if request.user.is_authenticated else None,
            feedback=feedback_obj,
            job=job_obj,
            severity=data["severity"],
            reason=data["reason"],
            action_taken=data.get("action_taken", ""),
        )

        # Increment report count on profile
        profile, _ = TechnicianProfile.objects.get_or_create(user=technician)
        profile.report_count += 1
        profile.save()

        return Response(
            {
                "message": f"Report filed against technician '{technician.username}'.",
                "report": TechnicianReportSerializer(report).data,
            },
            status=status.HTTP_201_CREATED,
        )


class ResolveReportView(APIView):
    """
    PATCH /api/v1/jobs/reports/<id>/resolve/
    Mark a report as resolved with action taken.
    """

    def patch(self, request, pk):
        try:
            report = TechnicianReport.objects.get(pk=pk)
        except TechnicianReport.DoesNotExist:
            return Response(
                {"error": "Report not found."}, status=status.HTTP_404_NOT_FOUND
            )

        report.is_resolved = True
        report.action_taken = request.data.get("action_taken", report.action_taken)
        report.save()

        return Response(
            {
                "message": "Report marked as resolved.",
                "report": TechnicianReportSerializer(report).data,
            }
        )


# ══════════════════════════════════════════════════════════════
# CONVERSATION VIEWS (Talk to Agent)
# ══════════════════════════════════════════════════════════════

class ConversationListView(generics.ListAPIView):
    """
    GET /api/v1/jobs/conversations/
    List all conversation sessions. Supports ?status=open
    """

    serializer_class = ConversationSessionSerializer
    queryset = ConversationSession.objects.select_related("customer", "agent", "job")

    def get_queryset(self):
        qs = super().get_queryset()
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class ConversationDetailView(APIView):
    """
    GET /api/v1/jobs/conversations/<id>/
    Get conversation details with all messages.
    """

    def get(self, request, pk):
        try:
            conversation = ConversationSession.objects.select_related(
                "customer", "agent", "job"
            ).get(pk=pk)
        except ConversationSession.DoesNotExist:
            return Response(
                {"error": "Conversation not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        messages = conversation.messages.select_related("sender").all()

        return Response(
            {
                "conversation": ConversationSessionSerializer(conversation).data,
                "messages": ChatMessageSerializer(messages, many=True).data,
            }
        )


class SendMessageView(APIView):
    """
    POST /api/v1/jobs/conversations/<id>/send/
    Agent sends a message in a conversation.
    """

    def post(self, request, pk):
        try:
            conversation = ConversationSession.objects.get(pk=pk)
        except ConversationSession.DoesNotExist:
            return Response(
                {"error": "Conversation not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        content = request.data.get("content", "").strip()
        if not content:
            return Response(
                {"error": "Message content is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sender_type = request.data.get("sender_type", "agent")

        msg = ChatMessage.objects.create(
            conversation=conversation,
            sender_type=sender_type,
            sender=request.user if request.user.is_authenticated else None,
            content=content,
        )

        # Notify customer via WhatsApp if agent sent it
        if sender_type == "agent":
            customer = conversation.customer
            cust_phone = customer.phone_number or customer.whatsapp_id
            if cust_phone:
                # We prefix with a small emoji so customer knows it's an agent.
                wa_msg = f"🧑‍💻 *Support Team:*\n{content}"
                send_whatsapp_message(cust_phone, wa_msg)

        # Update conversation status if needed
        if conversation.status == "open":
            conversation.status = "in_progress"
            conversation.save()

        return Response(
            {
                "message": "Message sent.",
                "chat_message": ChatMessageSerializer(msg).data,
            },
            status=status.HTTP_201_CREATED,
        )


class CloseConversationView(APIView):
    """
    POST /api/v1/jobs/conversations/<id>/close/
    Close/resolve a conversation session.
    """

    def post(self, request, pk):
        try:
            conversation = ConversationSession.objects.get(pk=pk)
        except ConversationSession.DoesNotExist:
            return Response(
                {"error": "Conversation not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        conversation.status = request.data.get("status", "resolved")
        conversation.closed_at = timezone.now()
        conversation.save()

        # Add system message
        ChatMessage.objects.create(
            conversation=conversation,
            sender_type="system",
            content=f"Conversation {conversation.get_status_display().lower()} by support team.",
        )

        return Response(
            {
                "message": f"Conversation #{conversation.pk} has been {conversation.get_status_display().lower()}.",
                "conversation": ConversationSessionSerializer(conversation).data,
            }
        )
