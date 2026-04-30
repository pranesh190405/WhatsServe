import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from jobs.models import Job, JobAssignment, TechnicianReport, ConversationSession, ChatMessage, Warranty
from feedback.models import Feedback
from users.models import User, TechnicianProfile
from whatsapp.models import ConversationState

def reset():
    print("Clearing transactional data...")
    JobAssignment.objects.all().delete()
    Job.objects.all().delete()
    TechnicianReport.objects.all().delete()
    ChatMessage.objects.all().delete()
    ConversationSession.objects.all().delete()
    Feedback.objects.all().delete()
    ConversationState.objects.all().delete()
    
    print("Removing customers...")
    User.objects.filter(role='customer').delete()

    print("Ensuring support and technicians exist...")
    # Support
    support, _ = User.objects.get_or_create(username='support1', defaults={'role': 'support', 'email': 'support1@test.com'})
    support.set_password('pass123')
    support.is_active = True
    support.role = 'support'
    support.save()

    # Technicians
    techs = [
        {'username': 'tech_ravi', 'first_name': 'Ravi', 'skills': 'AC Repair, Fridge', 'avail': 'available'},
        {'username': 'tech_amit', 'first_name': 'Amit', 'skills': 'Electrical, RO', 'avail': 'available'},
        {'username': 'tech_sarah', 'first_name': 'Sarah', 'skills': 'TV Repair, Audio', 'avail': 'busy'},
    ]
    for t in techs:
        user, _ = User.objects.get_or_create(username=t['username'], defaults={'first_name': t['first_name'], 'role': 'technician'})
        user.set_password('pass123')
        user.role = 'technician'
        user.save()
        profile, _ = TechnicianProfile.objects.get_or_create(user=user)
        profile.skills = t['skills']
        profile.availability = t['avail']
        profile.save()

    # Ensure some warranties exist so WhatsApp can look them up!
    from django.utils import timezone
    from datetime import timedelta
    now = timezone.now().date()
    Warranty.objects.get_or_create(serial_number="SN-12345", defaults={"product_name": "LG AC", "purchase_date": now - timedelta(days=100), "expiry_date": now + timedelta(days=200)})

    print("Reset complete! Ready for fresh WhatsApp booking.")

if __name__ == "__main__":
    reset()
