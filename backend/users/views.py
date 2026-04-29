import json
import io
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import User, TechnicianProfile
from .serializers import (
    TechnicianListSerializer,
    TechnicianCreateSerializer,
    TechnicianUpdateSerializer,
)


class TechnicianListView(generics.ListAPIView):
    """
    GET /api/v1/technicians/
    List all technicians with their profiles.
    Supports: ?availability=available, ?search=keyword
    """

    serializer_class = TechnicianListSerializer
    queryset = User.objects.filter(role="technician").select_related("technician_profile")

    def get_queryset(self):
        qs = super().get_queryset()
        availability = self.request.query_params.get("availability")
        search = self.request.query_params.get("search")

        if availability:
            qs = qs.filter(technician_profile__availability=availability)
        if search:
            qs = qs.filter(username__icontains=search) | qs.filter(
                first_name__icontains=search
            ) | qs.filter(last_name__icontains=search)
        return qs


class TechnicianCreateView(generics.CreateAPIView):
    """
    POST /api/v1/technicians/add/
    Create a single technician with profile.
    """

    serializer_class = TechnicianCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        detail = TechnicianListSerializer(user)
        return Response(
            {
                "message": f"Technician '{user.username}' created successfully.",
                "technician": detail.data,
            },
            status=status.HTTP_201_CREATED,
        )


class TechnicianDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/technicians/<id>/
    Retrieve a single technician's details.
    """

    serializer_class = TechnicianListSerializer
    queryset = User.objects.filter(role="technician").select_related("technician_profile")
    lookup_field = "pk"


class TechnicianUpdateView(APIView):
    """
    PATCH /api/v1/technicians/<id>/update/
    Update a technician and their profile.
    """

    def patch(self, request, pk):
        try:
            user = User.objects.get(pk=pk, role="technician")
        except User.DoesNotExist:
            return Response(
                {"error": "Technician not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = TechnicianUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(user, serializer.validated_data)

        detail = TechnicianListSerializer(user)
        return Response(
            {
                "message": f"Technician '{user.username}' updated successfully.",
                "technician": detail.data,
            }
        )


class TechnicianDeleteView(APIView):
    """
    DELETE /api/v1/technicians/<id>/delete/
    Delete a technician (deactivate).
    """

    def delete(self, request, pk):
        try:
            user = User.objects.get(pk=pk, role="technician")
        except User.DoesNotExist:
            return Response(
                {"error": "Technician not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        username = user.username
        user.is_active = False
        user.save()

        return Response(
            {"message": f"Technician '{username}' has been deactivated."},
            status=status.HTTP_200_OK,
        )


class TechnicianBulkImportView(APIView):
    """
    POST /api/v1/technicians/import/
    Bulk import technicians via JSON body or Excel file upload.

    JSON format:
    {
        "technicians": [
            {"username": "tech1", "first_name": "Ravi", "skills": "AC Repair", ...},
            {"username": "tech2", "first_name": "Suresh", "skills": "Plumbing", ...}
        ]
    }

    Excel format (.xlsx):
    Columns: username, first_name, last_name, email, phone_number, whatsapp_id, skills, availability, notes
    Any extra columns beyond these are stored in extra_fields as key-value pairs.
    """

    parser_classes = [MultiPartParser, FormParser, JSONParser]

    KNOWN_COLUMNS = {
        "username", "first_name", "last_name", "email",
        "phone_number", "whatsapp_id", "password",
        "skills", "availability", "notes",
    }

    def post(self, request):
        # Check if it's a file upload or JSON body
        file = request.FILES.get("file")

        if file:
            return self._import_from_file(file)
        elif "technicians" in request.data:
            return self._import_from_json(request.data["technicians"])
        else:
            return Response(
                {"error": "Provide either a file upload or JSON body with 'technicians' array."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def _import_from_json(self, technicians_data):
        """Import from JSON array."""
        created = []
        errors = []

        for i, tech_data in enumerate(technicians_data):
            try:
                serializer = TechnicianCreateSerializer(data=tech_data)
                serializer.is_valid(raise_exception=True)
                user = serializer.save()
                created.append(user.username)
            except Exception as e:
                errors.append({
                    "row": i + 1,
                    "username": tech_data.get("username", "unknown"),
                    "error": str(e),
                })

        return Response(
            {
                "message": f"Import complete. {len(created)} technicians created.",
                "created": created,
                "errors": errors,
                "total_processed": len(technicians_data),
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_400_BAD_REQUEST,
        )

    def _import_from_file(self, file):
        """Import from Excel (.xlsx) file."""
        filename = file.name.lower()

        if filename.endswith(".json"):
            return self._import_json_file(file)
        elif filename.endswith((".xlsx", ".xls")):
            return self._import_excel_file(file)
        else:
            return Response(
                {"error": "Unsupported file format. Use .xlsx or .json"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def _import_json_file(self, file):
        """Parse uploaded JSON file."""
        try:
            content = file.read().decode("utf-8")
            data = json.loads(content)

            if isinstance(data, list):
                technicians_data = data
            elif isinstance(data, dict) and "technicians" in data:
                technicians_data = data["technicians"]
            else:
                return Response(
                    {"error": "JSON must be an array or object with 'technicians' key."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return self._import_from_json(technicians_data)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            return Response(
                {"error": f"Invalid JSON file: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def _import_excel_file(self, file):
        """Parse uploaded Excel file. Extra columns go into extra_fields."""
        try:
            import openpyxl

            wb = openpyxl.load_workbook(io.BytesIO(file.read()), read_only=True)
            ws = wb.active

            rows = list(ws.iter_rows(values_only=True))
            if len(rows) < 2:
                return Response(
                    {"error": "Excel file must have a header row and at least one data row."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # First row = headers
            headers = [str(h).strip().lower() if h else "" for h in rows[0]]

            technicians_data = []
            for row in rows[1:]:
                tech = {}
                extra = {}
                for col_idx, header in enumerate(headers):
                    if not header:
                        continue
                    value = row[col_idx] if col_idx < len(row) else None
                    if value is None:
                        value = ""
                    value = str(value).strip()

                    if header in self.KNOWN_COLUMNS:
                        tech[header] = value
                    else:
                        # Extra column — store in extra_fields
                        extra[header] = value

                if extra:
                    tech["extra_fields"] = extra

                if tech.get("username"):
                    technicians_data.append(tech)

            wb.close()
            return self._import_from_json(technicians_data)

        except Exception as e:
            return Response(
                {"error": f"Failed to parse Excel file: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
