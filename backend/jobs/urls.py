from django.urls import path
from .views import (
    # Job CRUD
    CreateJobView,
    JobDetailView,
    JobListView,
    WarrantyCheckView,
    # Assignment
    AssignTechnicianView,
    AcceptAssignmentView,
    RejectAssignmentView,
    AssignmentListView,
    PendingReassignmentsView,
    # Feedback
    FeedbackListView,
    # Reports
    ReportListView,
    CreateReportView,
    ResolveReportView,
    # Conversations
    ConversationListView,
    ConversationDetailView,
    SendMessageView,
    CloseConversationView,
)

urlpatterns = [
    # ── Jobs ──
    path("", JobListView.as_view(), name="job-list"),
    path("create-job/", CreateJobView.as_view(), name="create-job"),
    path("job/<str:job_id>/", JobDetailView.as_view(), name="job-detail"),
    path("warranty/<str:serial_number>/", WarrantyCheckView.as_view(), name="warranty-check"),

    # ── Assignments ──
    path("job/<str:job_id>/assign/", AssignTechnicianView.as_view(), name="assign-technician"),
    path("assignments/", AssignmentListView.as_view(), name="assignment-list"),
    path("assignments/pending-reassignment/", PendingReassignmentsView.as_view(), name="pending-reassignment"),
    path("assignments/<int:pk>/accept/", AcceptAssignmentView.as_view(), name="accept-assignment"),
    path("assignments/<int:pk>/reject/", RejectAssignmentView.as_view(), name="reject-assignment"),

    # ── Feedback (support team view) ──
    path("feedback/", FeedbackListView.as_view(), name="feedback-list"),

    # ── Reports ──
    path("reports/", ReportListView.as_view(), name="report-list"),
    path("reports/create/", CreateReportView.as_view(), name="create-report"),
    path("reports/<int:pk>/resolve/", ResolveReportView.as_view(), name="resolve-report"),

    # ── Conversations (Talk to Agent) ──
    path("conversations/", ConversationListView.as_view(), name="conversation-list"),
    path("conversations/<int:pk>/", ConversationDetailView.as_view(), name="conversation-detail"),
    path("conversations/<int:pk>/send/", SendMessageView.as_view(), name="send-message"),
    path("conversations/<int:pk>/close/", CloseConversationView.as_view(), name="close-conversation"),
]
