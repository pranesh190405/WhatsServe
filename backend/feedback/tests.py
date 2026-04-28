from django.test import TestCase
from django.contrib.auth.models import User
from .models import Job, Feedback


class FeedbackModelTest(TestCase):
    """CRUD tests for the Feedback model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.job = Job.objects.create(
            title="Test Job", description="A test job posting"
        )

    # ---------- CREATE ----------
    def test_create_feedback(self):
        feedback = Feedback.objects.create(
            user=self.user, job=self.job, rating=5, comment="Excellent service!"
        )
        self.assertEqual(feedback.rating, 5)
        self.assertEqual(feedback.comment, "Excellent service!")
        self.assertEqual(feedback.user, self.user)
        self.assertEqual(feedback.job, self.job)
        self.assertIsNotNone(feedback.created_at)

    def test_create_feedback_without_comment(self):
        feedback = Feedback.objects.create(
            user=self.user, job=self.job, rating=3
        )
        self.assertEqual(feedback.comment, "")

    # ---------- READ ----------
    def test_read_feedback(self):
        Feedback.objects.create(
            user=self.user, job=self.job, rating=4, comment="Good"
        )
        fb = Feedback.objects.get(user=self.user, job=self.job)
        self.assertEqual(fb.rating, 4)
        self.assertEqual(fb.comment, "Good")

    def test_list_feedback(self):
        for i in range(1, 4):
            Feedback.objects.create(user=self.user, job=self.job, rating=i)
        self.assertEqual(Feedback.objects.count(), 3)

    # ---------- UPDATE ----------
    def test_update_feedback(self):
        feedback = Feedback.objects.create(
            user=self.user, job=self.job, rating=2, comment="Needs work"
        )
        feedback.rating = 4
        feedback.comment = "Much improved"
        feedback.save()
        feedback.refresh_from_db()
        self.assertEqual(feedback.rating, 4)
        self.assertEqual(feedback.comment, "Much improved")

    # ---------- DELETE ----------
    def test_delete_feedback(self):
        feedback = Feedback.objects.create(
            user=self.user, job=self.job, rating=1
        )
        pk = feedback.pk
        feedback.delete()
        self.assertFalse(Feedback.objects.filter(pk=pk).exists())

    # ---------- CONSTRAINTS ----------
    def test_str_representation(self):
        feedback = Feedback.objects.create(
            user=self.user, job=self.job, rating=5
        )
        self.assertIn("5★", str(feedback))
        self.assertIn("testuser", str(feedback))

    def test_feedback_ordering(self):
        """Newest feedback should appear first (ordering = -created_at)."""
        f1 = Feedback.objects.create(user=self.user, job=self.job, rating=1)
        f2 = Feedback.objects.create(user=self.user, job=self.job, rating=2)
        feedbacks = list(Feedback.objects.all())
        self.assertEqual(feedbacks[0], f2)
        self.assertEqual(feedbacks[1], f1)

    def test_cascade_delete_user(self):
        """Deleting a user should cascade-delete their feedback."""
        Feedback.objects.create(user=self.user, job=self.job, rating=3)
        self.user.delete()
        self.assertEqual(Feedback.objects.count(), 0)

    def test_cascade_delete_job(self):
        """Deleting a job should cascade-delete related feedback."""
        Feedback.objects.create(user=self.user, job=self.job, rating=3)
        self.job.delete()
        self.assertEqual(Feedback.objects.count(), 0)


class JobModelTest(TestCase):
    """Basic tests for the Job stub model."""

    def test_create_job(self):
        job = Job.objects.create(title="Plumbing Fix", description="Fix leak")
        self.assertEqual(job.title, "Plumbing Fix")
        self.assertIsNotNone(job.created_at)

    def test_str_representation(self):
        job = Job.objects.create(title="Painting Job")
        self.assertEqual(str(job), "Painting Job")
