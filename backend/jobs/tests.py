from datetime import date
from django.test import TestCase
from django.utils import timezone
from users.models import User
from .models import Job, Warranty


class JobModelTest(TestCase):
    """Tests for the Job model and auto-generated job IDs."""

    def setUp(self):
        self.customer = User.objects.create_user(
            username="testcustomer", password="testpass123", role="customer"
        )
        self.technician = User.objects.create_user(
            username="testtech", password="testpass123", role="technician"
        )

    def test_job_id_auto_generated(self):
        """Job ID should be auto-generated on save."""
        job = Job.objects.create(
            title="Test Service",
            description="Fix something",
            customer=self.customer,
        )
        self.assertTrue(job.job_id.startswith("JOB-"))
        self.assertEqual(len(job.job_id), 17)  # JOB-YYYYMMDD-XXXX

    def test_job_id_unique_per_day(self):
        """Multiple jobs on the same day should have sequential IDs."""
        job1 = Job.objects.create(
            title="Job 1", customer=self.customer
        )
        job2 = Job.objects.create(
            title="Job 2", customer=self.customer
        )
        # Both should share the same date prefix
        self.assertEqual(job1.job_id[:13], job2.job_id[:13])
        # But have different sequence numbers
        self.assertNotEqual(job1.job_id, job2.job_id)

    def test_job_default_status(self):
        """New jobs should default to 'pending' status."""
        job = Job.objects.create(
            title="Test", customer=self.customer
        )
        self.assertEqual(job.status, "pending")

    def test_job_str_representation(self):
        """Job __str__ should include job_id and title."""
        job = Job.objects.create(
            title="Fix AC", customer=self.customer
        )
        self.assertIn("Fix AC", str(job))
        self.assertIn("JOB-", str(job))


class WarrantyModelTest(TestCase):
    """Tests for the Warranty model."""

    def setUp(self):
        self.customer = User.objects.create_user(
            username="warrantycustomer", password="testpass123"
        )

    def test_valid_warranty(self):
        """Warranty with future expiry date should be valid."""
        warranty = Warranty.objects.create(
            serial_number="SN-001",
            product_name="Washing Machine",
            purchase_date=date(2025, 1, 1),
            expiry_date=date(2027, 1, 1),
            customer=self.customer,
        )
        self.assertTrue(warranty.is_valid)
        self.assertEqual(warranty.status_display, "Valid")

    def test_expired_warranty(self):
        """Warranty with past expiry date should be expired."""
        warranty = Warranty.objects.create(
            serial_number="SN-002",
            product_name="Old Fridge",
            purchase_date=date(2020, 1, 1),
            expiry_date=date(2022, 1, 1),
            customer=self.customer,
        )
        self.assertFalse(warranty.is_valid)
        self.assertEqual(warranty.status_display, "Expired")


class JobAPITest(TestCase):
    """Integration tests for the Job API endpoints."""

    def setUp(self):
        self.customer = User.objects.create_user(
            username="apicustomer", password="testpass123", role="customer"
        )

    def test_create_job_api(self):
        """POST /api/v1/jobs/create-job/ should create a job."""
        response = self.client.post(
            "/api/v1/jobs/create-job/",
            data={
                "customer_name": "apicustomer",
                "title": "AC Repair",
                "issue": "AC not cooling",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("job", response.json())
        self.assertTrue(response.json()["job"]["job_id"].startswith("JOB-"))

    def test_get_job_detail(self):
        """GET /api/v1/jobs/job/<job_id>/ should return job details."""
        job = Job.objects.create(
            title="Plumbing Fix",
            description="Leaky faucet",
            customer=self.customer,
        )
        response = self.client.get(f"/api/v1/jobs/job/{job.job_id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["job_id"], job.job_id)

    def test_list_jobs(self):
        """GET /api/v1/jobs/ should return a list of jobs."""
        Job.objects.create(title="Job A", customer=self.customer)
        Job.objects.create(title="Job B", customer=self.customer)
        response = self.client.get("/api/v1/jobs/")
        self.assertEqual(response.status_code, 200)

    def test_filter_jobs_by_status(self):
        """GET /api/v1/jobs/?status=pending should filter jobs."""
        Job.objects.create(title="Pending Job", customer=self.customer, status="pending")
        Job.objects.create(title="Done Job", customer=self.customer, status="completed")
        response = self.client.get("/api/v1/jobs/?status=pending")
        self.assertEqual(response.status_code, 200)


class WarrantyAPITest(TestCase):
    """Integration tests for the Warranty API endpoint."""

    def test_warranty_check_found(self):
        """GET /api/v1/jobs/warranty/<serial>/ should return warranty info."""
        customer = User.objects.create_user(
            username="wcustomer", password="testpass123"
        )
        Warranty.objects.create(
            serial_number="WM-12345",
            product_name="Washing Machine XL",
            purchase_date=date(2025, 1, 1),
            expiry_date=date(2027, 1, 1),
            customer=customer,
        )
        response = self.client.get("/api/v1/jobs/warranty/WM-12345/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("warranty", response.json())

    def test_warranty_check_not_found(self):
        """GET /api/v1/jobs/warranty/<serial>/ should 404 for unknown serial."""
        response = self.client.get("/api/v1/jobs/warranty/NONEXISTENT/")
        self.assertEqual(response.status_code, 404)
