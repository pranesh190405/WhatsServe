# WhatsServe — WhatsApp Service Support System

> A professional WhatsApp-integrated service management platform for electronics stores.
> Customers interact via WhatsApp to book repairs, check warranties, and track service requests.
> Support team manages everything from a modern React dashboard.

## Tech Stack

| Layer       | Technology                    |
|-------------|-------------------------------|
| Backend     | Django 5 + Django REST Framework |
| Database    | PostgreSQL                    |
| Frontend    | React (Vite) + Tailwind CSS   |
| Messaging   | Twilio WhatsApp API           |

## Quick Start

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env            # Edit with your credentials
python manage.py migrate
python populate_data.py         # Load test data
python manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Twilio Setup
1. Create a free account at [twilio.com](https://www.twilio.com)
2. Activate the WhatsApp Sandbox in the Twilio Console
3. Add your credentials to `backend/.env`:
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_WHATSAPP_NUMBER`
4. Use [ngrok](https://ngrok.com) to expose your local server:
   ```bash
   ngrok http 8000
   ```
5. Set the ngrok URL as your Twilio webhook:
   `https://your-ngrok-url/api/v1/whatsapp/webhook/`

## Project Structure

```
WhatsServe/
├── backend/
│   ├── config/          # Django settings, URLs, WSGI
│   ├── users/           # User model, Technician profiles, CRUD APIs
│   ├── jobs/            # Jobs, Assignments, Reports, Conversations
│   ├── feedback/        # Customer feedback model
│   ├── whatsapp/        # Twilio webhook, conversation state, message sender
│   └── populate_data.py # Test data seeder
├── frontend/
│   └── src/
│       ├── components/  # Dashboard, Jobs, Technicians, Live Chat, Feedback
│       └── services/    # Centralized API layer
└── docs/                # Sprint plan and documentation
```

## Developers
- **Dev 1 — Sanjeev Prakash** (Backend & Automation)
- **Dev 2 — M Pranesh** (Frontend & Integration)
