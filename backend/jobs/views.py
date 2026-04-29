from rest_framework import generics, status
from rest_framework.response import Response
from .models import Job, Warranty
from .serializers import JobCreateSerializer, JobDetailSerializer, WarrantySerializer


class CreateJobView(generics.CreateAPIView):
    """
    POST /api/v1/jobs/create-job/
    Create a new service job.

    Request body:
        - customer_name: str
        - title: str
        - issue: str (maps to description)

    Response:
        - job_id, title, status, customer_name, created_at
    """

    serializer_class = JobCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = serializer.save()

        # Return full detail response
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
