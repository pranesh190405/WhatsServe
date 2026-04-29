# n8n Workflow Design — WhatsServe

This document describes the n8n workflow that orchestrates the WhatsApp
conversational flow for the WhatsServe service support system.

## Overview

```
WhatsApp User → Meta Cloud API → Django Webhook → n8n Webhook
                                                      ↓
                                              Switch (choice)
                                          ┌────────┼────────┐
                                          1        2        3
                                      Book     Warranty   Track
                                     Service    Check    Request
                                          ↓        ↓        ↓
                                     POST       GET       GET
                                   /create-job /warranty/ /job/
                                          ↓        ↓        ↓
                                    Format Reply → Send WhatsApp Message
```

---

## Node-by-Node Breakdown

### Node 1: Webhook Trigger
- **Type**: Webhook
- **Method**: POST
- **Path**: `/webhook/whatsapp`
- **Purpose**: Receives the forwarded payload from Django with:
  ```json
  { "phone": "919876543210", "choice": "1", "raw_message": "1" }
  ```

### Node 2: Switch (Route by Choice)
- **Type**: Switch
- **Input**: `{{ $json.choice }}`
- **Rules**:
  | Value | Output | Description |
  |-------|--------|-------------|
  | `1`   | Output 0 | Book a Service flow |
  | `2`   | Output 1 | Check Warranty flow |
  | `3`   | Output 2 | Track Request flow  |
  | other | Fallback | Send error message  |

---

### Branch 1: Book a Service (choice = 1)

#### Node 1.1: HTTP Request — Create Job
- **Type**: HTTP Request
- **Method**: POST
- **URL**: `http://localhost:8000/api/v1/jobs/create-job/`
- **Body (JSON)**:
  ```json
  {
    "customer_name": "{{ $json.phone }}",
    "title": "Service Request via WhatsApp",
    "issue": "Customer initiated service booking via WhatsApp"
  }
  ```

#### Node 1.2: Format Reply
- **Type**: Set
- **Value**: Construct WhatsApp message from API response:
  ```
  ✅ Service booked successfully!

  📋 Job ID: {{ $json.job.job_id }}
  📌 Status: {{ $json.job.status_display }}

  We'll assign a technician shortly. Reply with 3 to track progress.
  ```

#### Node 1.3: Send WhatsApp Message
- **Type**: HTTP Request (Meta WhatsApp Cloud API)
- **Method**: POST
- **URL**: `https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages`
- **Headers**: `Authorization: Bearer {API_TOKEN}`
- **Body**: WhatsApp text message payload

---

### Branch 2: Check Warranty (choice = 2)

#### Node 2.1: Reply — Ask for Serial Number
- Send: "🔍 Please enter your product *serial number* to check warranty."

#### Node 2.2: Wait for Reply
- **Type**: Wait / Webhook (sub-workflow or session-based)
- Captures the user's next message as `serial_number`

#### Node 2.3: HTTP Request — Warranty Check
- **Method**: GET
- **URL**: `http://localhost:8000/api/v1/jobs/warranty/{{ $json.serial_number }}/`

#### Node 2.4: Format Reply
- If warranty found:
  ```
  🛡️ Warranty Status: {{ $json.warranty.status }}

  📦 Product: {{ $json.warranty.product_name }}
  📅 Expiry: {{ $json.warranty.expiry_date }}
  ```
- If not found:
  ```
  ❌ No warranty found for serial number {{ serial_number }}.
  ```

---

### Branch 3: Track Request (choice = 3)

#### Node 3.1: Reply — Ask for Job ID
- Send: "🔎 Please enter your *Job ID* (e.g. JOB-20260429-0001)."

#### Node 3.2: Wait for Reply
- Captures the user's next message as `job_id`

#### Node 3.3: HTTP Request — Get Job Status
- **Method**: GET
- **URL**: `http://localhost:8000/api/v1/jobs/job/{{ $json.job_id }}/`

#### Node 3.4: Format Reply
- If job found:
  ```
  📋 Job: {{ $json.job_id }}
  🏷️ Title: {{ $json.title }}
  📌 Status: {{ $json.status_display }}
  🛠️ Technician: {{ $json.technician_name || 'Not yet assigned' }}
  📅 Created: {{ $json.created_at }}
  ```
- If not found:
  ```
  ❌ No job found with ID {{ job_id }}. Please check and try again.
  ```

---

## Setup Instructions

1. Start n8n:
   ```bash
   docker-compose up -d
   ```
2. Open n8n at `http://localhost:5678`
3. Create a new workflow and add the nodes described above
4. Set the webhook path to `/webhook/whatsapp`
5. Activate the workflow
6. Update Django `.env` with the n8n webhook URL:
   ```
   N8N_WEBHOOK_URL=http://localhost:5678/webhook/whatsapp
   ```

## Error Handling

- All HTTP Request nodes should have **Continue On Fail** enabled
- On failure, send a friendly error message to the user via WhatsApp
- Log errors using the n8n Error Trigger node for monitoring

## Scalability Notes

- For production, use n8n Cloud or a dedicated n8n server with PostgreSQL backend
- Use n8n's built-in credentials manager for API tokens
- Consider adding rate limiting at the Django webhook level
- Use Redis-backed sessions for multi-step conversations (warranty/track flows)
