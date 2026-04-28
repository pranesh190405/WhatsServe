# WhatsServe

A Django + React platform for service management, feedback collection, and automation.

## Tech Stack

- **Backend**: Django 5.x, Django REST Framework, PostgreSQL
- **Frontend**: React 19 (Vite), Tailwind CSS v4
- **Automation**: n8n (webhook integration via DRF API)

## Project Structure

```
WhatsServe/
├── backend/          # Django project
│   ├── config/       # Project settings & URLs
│   └── feedback/     # Feedback app (model, API, admin)
├── frontend/         # Vite React app
│   └── src/
│       └── components/
└── README.md
```

## Getting Started

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
cp .env.example .env        # Configure your credentials
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

| Method | Endpoint              | Description            |
| ------ | --------------------- | ---------------------- |
| GET    | `/api/v1/feedback/`   | List all feedback      |
| POST   | `/api/v1/feedback/`   | Create new feedback    |
| GET    | `/api/v1/feedback/:id/` | Retrieve feedback    |
| PUT    | `/api/v1/feedback/:id/` | Update feedback      |
| DELETE | `/api/v1/feedback/:id/` | Delete feedback      |

## Environment Variables

See `backend/.env.example` for required configuration.
