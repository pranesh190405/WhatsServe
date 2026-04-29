# WhatsServe — Project Sprint Plan

> **Project:** WhatsApp-based Service Support System for an Electronics Store  
> **Stack:** Django + DRF · PostgreSQL · React (Vite) + Tailwind · Twilio WhatsApp API  
> **Developers:**  
> - **Dev 1 — Sanjeev Prakash** (Backend & Automation lead)  
> - **Dev 2 — M Pranesh** (Frontend & Integration lead)

---

## File Ownership Rules (Merge-Conflict Prevention)

To ensure both developers can commit independently without merge conflicts, each developer **owns** specific directories and files. **Never edit another developer's owned files without coordinating first.**

| Area | Dev 1 (Sanjeev) Owns | Dev 2 (Pranesh) Owns |
|------|-----------------------|----------------------|
| **Backend** | `users/`, `whatsapp/`, `jobs/views.py`, `jobs/models.py`, `jobs/serializers.py` | `feedback/`, `jobs/admin.py`, `jobs/urls.py`, `config/`, `populate_data.py` |
| **Frontend** | `components/JobsTable.jsx`, `components/TechniciansPage.jsx`, `components/LiveChatPage.jsx` | `components/Dashboard.jsx`, `components/FeedbackReportsPage.jsx`, `components/Sidebar.jsx`, `components/Topbar.jsx`, `components/DashboardLayout.jsx`, `services/api.js`, `index.css`, `App.jsx` |
| **Shared** | `requirements.txt` (coordinate), `docs/` | `package.json` (coordinate) |

---

## SPRINT 1: SYSTEM SETUP & FOUNDATION ✅

**Status:** COMPLETED  
**Duration:** 1 week

### Component 1.1 — Project & Environment Setup

| Task | Developer | Deliverable | Status |
|------|-----------|-------------|--------|
| Setup Django project with `config/` structure, `manage.py`, virtual env | Dev 1 | Runnable Django server on `:8000` | ✅ Done |
| Setup React (Vite) project with proper folder structure | Dev 1 | Runnable React dev server on `:5173` | ✅ Done |
| Configure PostgreSQL database (`whatsserve` DB) with env vars | Dev 2 | Django connects to PostgreSQL, migrations run | ✅ Done |
| Configure Tailwind CSS with custom design tokens (light theme) | Dev 2 | `index.css` with design system variables, Inter font | ✅ Done |

### Component 1.2 — Database Models

| Task | Developer | Deliverable | Status |
|------|-----------|-------------|--------|
| Create `User` model (Customer, Technician, Support, Admin roles) with `phone_number`, `whatsapp_id` fields | Dev 1 | `users/models.py` — `User` with role choices | ✅ Done |
| Create `TechnicianProfile` model with skills, availability, rating, and JSON `extra_fields` | Dev 1 | `users/models.py` — `TechnicianProfile` with OneToOne to User | ✅ Done |
| Create `Job` model with auto-generated `JOB-YYYYMMDD-XXXX` IDs, status tracking, customer/technician FKs | Dev 1 | `jobs/models.py` — `Job` with `generate_job_id()` | ✅ Done |
| Create `Warranty` model with serial number lookup and validity check | Dev 1 | `jobs/models.py` — `Warranty` with `is_valid` property | ✅ Done |
| Create `JobAssignment` model with 30-minute deadline, rejection tracking | Dev 1 | `jobs/models.py` — `JobAssignment` with auto-deadline | ✅ Done |
| Create `TechnicianReport` model with severity levels | Dev 1 | `jobs/models.py` — `TechnicianReport` | ✅ Done |
| Create `ConversationSession` and `ChatMessage` models for live chat | Dev 1 | `jobs/models.py` — Talk-to-agent data models | ✅ Done |
| Create `Feedback` model with 1-5 star rating and job FK | Dev 2 | `feedback/models.py` — `Feedback` | ✅ Done |
| Register all models in Django admin with proper filters, search, inlines | Dev 2 | `*/admin.py` files configured | ✅ Done |
| Run migrations and verify all models work via admin panel | Dev 2 | All tables created in PostgreSQL | ✅ Done |

### Component 1.3 — Base UI & Structure

| Task | Developer | Deliverable | Status |
|------|-----------|-------------|--------|
| Create collapsible Sidebar with navigation icons for all pages | Dev 2 | `Sidebar.jsx` with Dashboard, Jobs, Technicians, Live Chat, Feedback, Automation, Settings nav items | ✅ Done |
| Create Topbar with user info display | Dev 2 | `Topbar.jsx` | ✅ Done |
| Create Dashboard layout wrapper | Dev 2 | `DashboardLayout.jsx` composing Sidebar + Topbar + content area | ✅ Done |
| Create Dashboard overview page with live stats from API | Dev 2 | `Dashboard.jsx` with stat cards (Total, Pending, In Progress, Completed) | ✅ Done |
| Create centralized API service layer with Axios | Dev 2 | `services/api.js` with all endpoint functions | ✅ Done |
| Setup page-level routing via `App.jsx` | Dev 2 | `App.jsx` with `activePage` state switch | ✅ Done |

### Component 1.4 — WhatsApp Setup (Twilio)

| Task | Developer | Deliverable | Status |
|------|-----------|-------------|--------|
| Install `twilio` Python SDK and configure env vars (`TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_NUMBER`) | Dev 1 | `requirements.txt` updated, `.env.example` updated | ✅ Done |
| Build `send_whatsapp_message()` helper using Twilio Client | Dev 1 | `whatsapp/views.py` — working Twilio sender | ✅ Done |
| Build WhatsApp webhook view that parses Twilio's incoming message format (`From`, `Body`) | Dev 1 | `whatsapp/views.py` — `WhatsAppWebhookView` | ✅ Done |

**Sprint 1 Commits:**
1. `feat(backend): setup Django project, PostgreSQL config, all database models`
2. `feat(frontend): setup Vite + Tailwind, dashboard layout, sidebar, API service`
3. `feat(backend): integrate Twilio SDK, refactor WhatsApp webhook`

---

## SPRINT 2: WHATSAPP BOT & JOB CREATION ✅

**Status:** COMPLETED  
**Duration:** 1 week

### Component 2.1 — WhatsApp Bot Conversational Flow

| Task | Developer | Deliverable | Status |
|------|-----------|-------------|--------|
| Build welcome message menu sent on first contact: "1️⃣ Book a Service, 2️⃣ Check Warranty, 3️⃣ Track Request" | Dev 1 | User texts anything → receives welcome menu | ✅ Done |
| Handle user input "1" → Trigger service booking flow. Ask for issue description, create job via Django API, reply with Job ID | Dev 1 | Full booking flow: ask issue → create job → confirm with JOB-ID | ✅ Done |
| Handle user input "2" → Trigger warranty check flow. Ask for serial number, look up warranty, reply with status | Dev 1 | Full warranty flow: ask serial → check DB → reply Valid/Expired | ✅ Done |
| Handle user input "3" → Trigger job tracking flow. Ask for Job ID, look up status, reply with details | Dev 1 | Full tracking flow: ask job ID → look up → reply with status/technician info | ✅ Done |
| Handle edge cases: invalid input → repeat menu; timeouts → reset conversation state | Dev 2 | Graceful error handling, "I didn't understand" replies | ✅ Done |
| Implement per-user conversation state management to track multi-step flows (e.g., "waiting for serial number") | Dev 1 | `whatsapp/models.py` — `ConversationState` model with session tracking | ✅ Done |

### Component 2.2 — Job APIs & Logic

| Task | Developer | Deliverable | Status |
|------|-----------|-------------|--------|
| `POST /api/v1/jobs/create-job/` — accepts `customer_name`, `title`, `issue`, returns created job with auto-generated ID | Dev 1 | `CreateJobView` with `JobCreateSerializer` | ✅ Done |
| `GET /api/v1/jobs/` — list all jobs with filters (`?status=`, `?search=`) and pagination | Dev 1 | `JobListView` with query param filtering | ✅ Done |
| `GET /api/v1/jobs/job/<job_id>/` — retrieve single job by human-readable ID | Dev 1 | `JobDetailView` with `select_related` | ✅ Done |
| `GET /api/v1/jobs/warranty/<serial>/` — check warranty validity by serial number | Dev 1 | `WarrantyCheckView` with Valid/Expired response | ✅ Done |
| `POST /api/v1/jobs/job/<job_id>/assign/` — assign technician with 30-min deadline | Dev 1 | `AssignTechnicianView` with WhatsApp notification | ✅ Done |
| `GET /api/v1/jobs/assignments/pending-reassignment/` — list rejected/expired assignments | Dev 1 | `PendingReassignmentsView` | ✅ Done |
| `GET /api/v1/jobs/feedback/` — support team views customer feedback | Dev 1 | `FeedbackListView` | ✅ Done |
| `POST /api/v1/jobs/reports/create/` — file technician report | Dev 1 | `CreateReportView` | ✅ Done |
| Technician CRUD APIs: list, add, update, delete, bulk import (JSON/Excel) | Dev 1 | `users/views.py` — full technician management | ✅ Done |
| Conversation/Chat APIs: list sessions, get messages, send reply, close session | Dev 1 | `ConversationListView`, `SendMessageView`, etc. | ✅ Done |

### Component 2.3 — Job Dashboard UI

| Task | Developer | Deliverable | Status |
|------|-----------|-------------|--------|
| Build Jobs Table with columns: Job ID, Customer, Issue, Status, Technician, Created, Actions | Dev 1 | `JobsTable.jsx` — sortable table with status badges | ✅ Done |
| Add "Assign" button on pending jobs that opens technician selection modal | Dev 1 | Assign modal with available technician list, search, skill tags | ✅ Done |
| Add reassignment alert banner when jobs have rejected/expired assignments | Dev 1 | Red warning banner with count of jobs needing reassignment | ✅ Done |
| Add search and filter controls (by status, keyword) | Dev 1 | Filter bar above table | ✅ Done |
| Auto-refresh job list every 30 seconds | Dev 2 | `setInterval` with background fetch | ✅ Done |

### Component 2.4 — Support Team Pages

| Task | Developer | Deliverable | Status |
|------|-----------|-------------|--------|
| Build Technicians page: list, add form (with extra columns support), import modal (JSON/Excel) | Dev 1 | `TechniciansPage.jsx` — full CRUD UI with import | ✅ Done |
| Build Feedback & Reports page: tab switcher, feedback cards with star ratings, reports table with severity | Dev 2 | `FeedbackReportsPage.jsx` — dual-tab view | ✅ Done |
| Build Live Chat page: conversation list sidebar + chat window with WhatsApp relay | Dev 1 | `LiveChatPage.jsx` — real-time messaging interface | ✅ Done |
| Populate database with realistic test data for demo | Dev 2 | `populate_data.py` — creates technicians, customers, jobs, feedback, chats | ✅ Done |

**Sprint 2 Commits:**
1. `feat(backend): implement full WhatsApp bot with Twilio (booking, warranty, tracking flows)`
2. `feat(backend): add conversation state management for multi-step WhatsApp flows`
3. `feat(frontend): jobs table with assignment, technicians page, feedback & reports, live chat`
4. `chore: populate test data for demo`

---

## SPRINT 3: TECHNICIAN ASSIGNMENT & MANAGEMENT

**Status:** PENDING  
**Duration:** 1 week

### Component 3.1 — WhatsApp Technician Flow

| Task | Developer | Deliverable |
|------|-----------|-------------|
| When a job is assigned, send WhatsApp to technician: "🔧 New Job: JOB-ID. Title: X. Reply ACCEPT or REJECT." | Dev 1 | Twilio message sent on assignment |
| Parse technician WhatsApp replies: "ACCEPT JOB-xxx" → accept assignment, update status | Dev 1 | Webhook handles accept flow |
| Parse technician WhatsApp replies: "REJECT JOB-xxx [reason]" → reject, increment counter, alert support | Dev 1 | Webhook handles reject + auto-notify |
| If no response in 30 min, mark assignment as expired. Support team sees alert in dashboard | Dev 2 | Background task (Django management command) checks deadlines every 5 min |

### Component 3.2 — Assignment UI

| Task | Developer | Deliverable |
|------|-----------|-------------|
| Show assignment history on job detail (who was assigned, accepted/rejected/expired timeline) | Dev 2 | Assignment history section in job detail modal |
| Show real-time assignment status badge on technician cards | Dev 1 | "Currently on Job: JOB-xxx" indicator |

### Component 3.3 — Job Filtering & Search

| Task | Developer | Deliverable |
|------|-----------|-------------|
| Add date range filtering to jobs table | Dev 2 | Date picker filter |
| Add sorting by columns (created date, status) | Dev 2 | Clickable column headers |
| Add pagination controls | Dev 2 | Page navigation below table |

---

## SPRINT 4: SERVICE COMPLETION & OTP FLOW

**Status:** PENDING  
**Duration:** 1 week

### Component 4.1 — Completion Detection

| Task | Developer | Deliverable |
|------|-----------|-------------|
| Technician sends "DONE JOB-xxx" via WhatsApp → webhook detects and initiates OTP flow | Dev 1 | Webhook parsing for DONE command |
| Validate that the technician sending DONE is the one assigned to the job | Dev 1 | Auth check in webhook |

### Component 4.2 — OTP System

| Task | Developer | Deliverable |
|------|-----------|-------------|
| Generate random 4-digit OTP, save to Job model (new `otp` and `otp_expires_at` fields) | Dev 1 | OTP generation logic |
| Send OTP to customer via WhatsApp: "Your technician says the job is done. Share this OTP: XXXX" | Dev 1 | Twilio OTP message |
| Technician receives OTP from customer, sends "OTP XXXX" via WhatsApp → validate and complete job | Dev 1 | OTP validation, job status → completed |
| Update job status UI to show "Awaiting OTP" state | Dev 2 | New status badge color |

### Component 4.3 — Job Status UI Enhancements

| Task | Developer | Deliverable |
|------|-----------|-------------|
| Add color-coded status indicators throughout dashboard | Dev 2 | Consistent badge system |
| Show job timeline/history (created → assigned → accepted → OTP → completed) | Dev 2 | Timeline component |

---

## SPRINT 5: FEEDBACK, SUPPORT PANEL & AUTOMATION

**Status:** PENDING  
**Duration:** 1 week

### Component 5.1 — Automated Feedback Collection

| Task | Developer | Deliverable |
|------|-----------|-------------|
| After job completion (OTP verified), auto-send feedback request via WhatsApp: "Rate 1-5" | Dev 1 | Post-completion trigger |
| Parse customer rating reply, save to Feedback model | Dev 1 | Webhook feedback handler |
| If customer sends comment after rating, append to feedback | Dev 1 | Multi-step feedback flow |

### Component 5.2 — Automation Logic

| Task | Developer | Deliverable |
|------|-----------|-------------|
| Django management command `check_expired_assignments` — runs every 5 min via cron/scheduler | Dev 1 | `management/commands/check_expired_assignments.py` |
| Auto-notify support team dashboard when assignments expire | Dev 2 | Real-time alert badge on sidebar |
| Handle incomplete jobs (no OTP after 24h → auto-flag for support review) | Dev 1 | Cleanup command |

### Component 5.3 — Support Panel Enhancements

| Task | Developer | Deliverable |
|------|-----------|-------------|
| Real-time notification count on sidebar (open chats, pending assignments) | Dev 2 | Badge counters |
| Highlight low-rating feedback (≤ 2 stars) with warning styling | Dev 2 | Conditional styling in feedback cards |
| One-click "Report Technician" from feedback card | Dev 2 | Pre-filled report modal |

### Component 5.4 — Analytics Dashboard

| Task | Developer | Deliverable |
|------|-----------|-------------|
| Technician performance chart (jobs completed, avg rating) | Dev 2 | Chart component on Dashboard |
| Job volume trends (daily/weekly) | Dev 2 | Line chart on Dashboard |
| Support response time metrics | Dev 2 | Stat cards |
