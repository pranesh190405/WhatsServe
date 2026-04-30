# WhatsServe Setup Instructions (Windows / Mac / Linux)

Follow these steps to set up the WhatsServe platform on a completely fresh computer.

---

## 1. Prerequisites
Ensure the new computer has the following installed:
- **Python 3.10+**
- **Node.js 18+** (for the React frontend)
- **PostgreSQL** (Running locally on port 5432)
- **Redis** (Running locally on port 6379)
  - *Mac/Linux:* `brew install redis` or `sudo apt install redis`
  - *Windows:* Use [Memurai](https://www.memurai.com/) (Redis for Windows) or WSL.

---

## 2. Backend Setup (Django + Celery)

1. **Clone the repository** and open a terminal in the `backend` folder.
2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   
   # Windows:
   .venv\Scripts\activate
   # Mac/Linux:
   source .venv/bin/activate
   ```
3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Environment Variables:**
   Copy `.env.example` to a new file named `.env` and fill in your keys:
   - `DB_PASSWORD` (Your PostgreSQL password)
   - `GEMINI_API_KEY` (Your Google Gemini AI Key)
   - `TWILIO_ACCOUNT_SID` & `TWILIO_AUTH_TOKEN`

5. **Database Setup:**
   Create a database named `whatsserve` in PostgreSQL. Then run:
   ```bash
   python manage.py makemigrations users jobs feedback whatsapp
   python manage.py migrate
   python reset_data.py  # (Optional: Populates the admin user and technicians)
   ```

---

## 3. Frontend Setup (React + Vite)

1. Open a new terminal in the `frontend` folder.
2. **Install Node dependencies:**
   ```bash
   npm install
   ```
3. **Environment Variables:**
   Create a `.env` file in the `frontend` folder with the following:
   ```env
   VITE_API_URL=http://localhost:8000/api/v1
   ```

---

## 4. How to Start the Entire System

To run the full production architecture locally, you need **4 separate terminal windows**. 

### Terminal 1: Django Server
```bash
cd backend
.venv\Scripts\activate
python manage.py runserver
```

### Terminal 2: Celery Worker (Crucial for WhatsApp Bot)
*If you do not run this, the WhatsApp bot will receive messages but will never reply!*
```bash
cd backend
.venv\Scripts\activate
celery -A config worker -l info -P solo
```

### Terminal 3: Ngrok (For Twilio Webhooks)
```bash
cd backend
.venv\Scripts\activate
python start_ngrok.py
```
*(Copy the generated webhook URL into your Twilio Console).*

### Terminal 4: React Dashboard
```bash
cd frontend
npm run dev
```

You can now log into the frontend at `http://localhost:5173/` using the `support1` user, and text your Twilio number to use the AI bot!
