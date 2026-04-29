import os
import django
from django.utils import timezone
from datetime import timedelta
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User, TechnicianProfile
from jobs.models import Job, Warranty, JobAssignment, TechnicianReport, ConversationSession, ChatMessage
from feedback.models import Feedback

def populate():
    print("Populating test data...")

    # 1. Create Admins/Support
    print("Creating Support/Admin users...")
    support, _ = User.objects.get_or_create(username='support1', defaults={'role': 'support', 'email': 'support1@test.com'})
    support.set_password('pass123')
    support.save()

    # 2. Create Technicians
    print("Creating Technicians...")
    techs = [
        {'username': 'tech_ravi', 'first_name': 'Ravi', 'skills': 'AC Repair, Fridge', 'avail': 'available', 'rating': 4.5, 'jobs': 12},
        {'username': 'tech_suresh', 'first_name': 'Suresh', 'skills': 'Plumbing, AC', 'avail': 'busy', 'rating': 3.8, 'jobs': 8},
        {'username': 'tech_amit', 'first_name': 'Amit', 'skills': 'Electrical, RO', 'avail': 'available', 'rating': 4.8, 'jobs': 20},
        {'username': 'tech_raj', 'first_name': 'Raj', 'skills': 'TV Repair', 'avail': 'offline', 'rating': 2.5, 'jobs': 3, 'reports': 1},
    ]
    
    tech_objs = []
    for t in techs:
        user, _ = User.objects.get_or_create(username=t['username'], defaults={'first_name': t['first_name'], 'role': 'technician'})
        user.set_password('pass123')
        user.save()
        profile, _ = TechnicianProfile.objects.get_or_create(user=user)
        profile.skills = t['skills']
        profile.availability = t['avail']
        profile.average_rating = t['rating']
        profile.total_jobs_completed = t['jobs']
        profile.report_count = t.get('reports', 0)
        profile.save()
        tech_objs.append(user)

    # 3. Create Customers
    print("Creating Customers...")
    customers = []
    for i in range(1, 6):
        cust, _ = User.objects.get_or_create(username=f'customer{i}', defaults={'role': 'customer', 'phone_number': f'987654321{i}'})
        customers.append(cust)

    # 4. Create Jobs & Assignments
    print("Creating Jobs and Assignments...")
    now = timezone.now()
    
    # Completed Job
    job1, _ = Job.objects.get_or_create(title="AC not cooling", customer=customers[0], defaults={'status': 'completed', 'technician': tech_objs[0], 'description': 'Customer reported AC is blowing warm air.'})
    JobAssignment.objects.get_or_create(job=job1, technician=tech_objs[0], defaults={'status': 'accepted', 'assigned_by': support, 'assigned_at': now - timedelta(days=2), 'responded_at': now - timedelta(days=2)})
    Feedback.objects.get_or_create(job=job1, user=customers[0], defaults={'rating': 5, 'comment': 'Excellent service, very polite.'})
    
    # Job with bad feedback and report
    job2, _ = Job.objects.get_or_create(title="TV screen blinking", customer=customers[1], defaults={'status': 'completed', 'technician': tech_objs[3], 'description': 'Screen flickers constantly.'})
    JobAssignment.objects.get_or_create(job=job2, technician=tech_objs[3], defaults={'status': 'accepted', 'assigned_by': support, 'assigned_at': now - timedelta(days=5), 'responded_at': now - timedelta(days=5)})
    fb, _ = Feedback.objects.get_or_create(job=job2, user=customers[1], defaults={'rating': 2, 'comment': 'Arrived late, and the TV is still acting up sometimes.'})
    TechnicianReport.objects.get_or_create(technician=tech_objs[3], feedback=fb, job=job2, defaults={'reported_by': support, 'severity': 'medium', 'reason': 'Late arrival and incomplete repair.', 'action_taken': 'Warned.'})

    # In Progress Job
    job3, _ = Job.objects.get_or_create(title="Kitchen sink leaking", customer=customers[2], defaults={'status': 'in_progress', 'technician': tech_objs[1], 'description': 'Pipe under sink is leaking water.'})
    JobAssignment.objects.get_or_create(job=job3, technician=tech_objs[1], defaults={'status': 'accepted', 'assigned_by': support, 'assigned_at': now - timedelta(hours=2), 'responded_at': now - timedelta(hours=1)})

    # Pending Job
    job4, _ = Job.objects.get_or_create(title="RO Water Purifier installation", customer=customers[3], defaults={'status': 'pending', 'description': 'Need to install new water purifier.'})

    # Job needing reassignment (Rejected)
    job5, _ = Job.objects.get_or_create(title="Microwave stopped working", customer=customers[4], defaults={'status': 'pending', 'description': 'Does not heat up anymore.'})
    JobAssignment.objects.get_or_create(job=job5, technician=tech_objs[2], defaults={'status': 'rejected', 'assigned_by': support, 'assigned_at': now - timedelta(hours=1), 'responded_at': now - timedelta(minutes=50), 'rejection_reason': 'Too far from my location.'})

    # Job needing reassignment (Expired)
    job6, _ = Job.objects.get_or_create(title="Fridge not cooling", customer=customers[0], defaults={'status': 'pending', 'description': 'Freezer works, but bottom is warm.'})
    JobAssignment.objects.get_or_create(job=job6, technician=tech_objs[0], defaults={'status': 'expired', 'assigned_by': support, 'assigned_at': now - timedelta(hours=2), 'deadline': now - timedelta(hours=1, minutes=30)})


    # 5. Create Live Chat Conversations
    print("Creating Live Chat Sessions...")
    
    # Active chat
    conv1, _ = ConversationSession.objects.get_or_create(customer=customers[2], job=job3, defaults={'status': 'in_progress', 'agent': support, 'subject': 'Query about pricing'})
    ChatMessage.objects.get_or_create(conversation=conv1, sender_type='customer', content='Hi, what will be the visiting charge?', defaults={'sender': customers[2]})
    ChatMessage.objects.get_or_create(conversation=conv1, sender_type='agent', content='Hello! The visiting charge is ₹250.', defaults={'sender': support})
    ChatMessage.objects.get_or_create(conversation=conv1, sender_type='customer', content='Okay, thanks.', defaults={'sender': customers[2]})

    # New chat
    conv2, _ = ConversationSession.objects.get_or_create(customer=customers[4], defaults={'status': 'open', 'subject': 'General Inquiry'})
    ChatMessage.objects.get_or_create(conversation=conv2, sender_type='customer', content='Do you guys repair washing machines?', defaults={'sender': customers[4]})

    # Resolved chat
    conv3, _ = ConversationSession.objects.get_or_create(customer=customers[0], job=job1, defaults={'status': 'resolved', 'agent': support, 'subject': 'AC Repair timeline'})
    ChatMessage.objects.get_or_create(conversation=conv3, sender_type='customer', content='How long will it take?', defaults={'sender': customers[0]})
    ChatMessage.objects.get_or_create(conversation=conv3, sender_type='agent', content='Usually 1-2 hours.', defaults={'sender': support})
    ChatMessage.objects.get_or_create(conversation=conv3, sender_type='system', content='Conversation resolved by support team.')

    print("Data population complete!")

if __name__ == '__main__':
    populate()
