import os
import json
import random
import logging
from google import genai
from google.genai import types
from twilio.rest import Client

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# Twilio Configuration
# ──────────────────────────────────────────────────────────────

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "")

_twilio_client = None

def get_twilio_client():
    global _twilio_client
    if _twilio_client is None and TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
        _twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    return _twilio_client

def send_whatsapp_message(to, text):
    """
    Send a WhatsApp message via Twilio.
    """
    client = get_twilio_client()
    if not client:
        logger.warning("Twilio credentials not configured. Skipping WhatsApp send to %s", to)
        return None

    if not to.startswith("whatsapp:"):
        to = f"whatsapp:{to}"

    from_number = TWILIO_WHATSAPP_NUMBER
    if not from_number.startswith("whatsapp:"):
        from_number = f"whatsapp:{from_number}"

    try:
        message = client.messages.create(
            body=text,
            from_=from_number,
            to=to,
        )
        logger.info("WhatsApp message sent to %s — SID: %s", to, message.sid)
        return message.sid
    except Exception as e:
        logger.error("Failed to send WhatsApp message to %s: %s", to, e)
        return None


# ──────────────────────────────────────────────────────────────
# Gemini AI Configuration
# ──────────────────────────────────────────────────────────────

_gemini_client = None

def get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key and api_key != "your-gemini-api-key-here":
            _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client


def analyze_intent(user_text):
    """
    Analyzes the user's text using Gemini to determine their intent.
    Handles natural language like "My AC is leaking" or "I want to check warranty".
    
    Returns a dict like:
    {
        "intent": "BOOK_SERVICE" | "CHECK_WARRANTY" | "TRACK_REQUEST" | "TALK_TO_AGENT" | "UNKNOWN",
        "category": "appliance type if found" | null,
        "issue": "issue description if found" | null,
        "serial": "serial number if found" | null,
        "job_id": "job id if found" | null
    }
    """
    client = get_gemini_client()
    
    # Fallback if Gemini is not configured
    if not client:
        logger.warning("Gemini client not configured. Falling back to keyword matching.")
        return _fallback_intent_analyzer(user_text)

    prompt = f"""You are a smart router for an electronics after-sales service WhatsApp bot called WhatsServe.

The user sent a message. Determine their intent and extract any relevant entities.

Valid intents:
- BOOK_SERVICE: User wants to book a repair/service. Look for mentions of appliance problems, breakdowns, repairs, etc.
- CHECK_WARRANTY: User wants to check warranty status. Look for serial numbers or warranty mentions.
- TRACK_REQUEST: User wants to track an existing job. Look for job IDs (format JOB-XXXXXXXX-XXXX) or words like "track", "status", "update".
- TALK_TO_AGENT: User wants to speak with a human agent. Look for words like "agent", "human", "help", "talk", "support".
- UNKNOWN: If none of the above match clearly.

For BOOK_SERVICE, also extract:
- "category": The appliance type (e.g., "Air Conditioner", "Refrigerator", "Washing Machine", "TV", "Microwave"). Standardize the name.
- "issue": A brief clean summary of the problem if described.

For CHECK_WARRANTY, extract:
- "serial": Any serial number mentioned.

For TRACK_REQUEST, extract:
- "job_id": Any job ID mentioned.

User message: "{user_text}"
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "OBJECT",
                    "properties": {
                        "intent": {"type": "STRING"},
                        "category": {"type": "STRING", "nullable": True},
                        "issue": {"type": "STRING", "nullable": True},
                        "serial": {"type": "STRING", "nullable": True},
                        "job_id": {"type": "STRING", "nullable": True}
                    },
                    "required": ["intent"]
                },
                temperature=0.0
            )
        )
        content = response.text
        result = json.loads(content)
        logger.info("Gemini intent result: %s", result)
        return result
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return _fallback_intent_analyzer(user_text)


def extract_appliance_category(user_text):
    """
    Use Gemini to extract the appliance category from user's natural text.
    Returns a clean standardized appliance name or None.
    """
    client = get_gemini_client()
    if not client:
        # Simple fallback — just return the text cleaned up
        return user_text.strip().title()

    prompt = f"""Extract the appliance/product type from this text. Return ONLY the standardized appliance name.
Common types: Air Conditioner, Refrigerator, Washing Machine, Television, Microwave, Water Purifier, Dishwasher, Geyser/Water Heater, Chimney, Oven.
If no clear appliance is mentioned, return the best guess based on context.

Text: "{user_text}"

Return just the appliance name, nothing else."""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.0)
        )
        result = response.text.strip().strip('"').strip("'")
        logger.info("Extracted appliance category: %s", result)
        return result
    except Exception as e:
        logger.error(f"Gemini category extraction error: {e}")
        return user_text.strip().title()


def summarize_issue(user_text, appliance=None):
    """
    Use Gemini to clean up the user's issue description into a professional summary.
    """
    client = get_gemini_client()
    if not client:
        return user_text.strip()

    context = f" for a {appliance}" if appliance else ""
    prompt = f"""Summarize this customer's service complaint{context} into a clear, professional one-line description suitable for a service ticket. Keep it under 100 characters.

Customer said: "{user_text}"

Return only the summary, nothing else."""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.0)
        )
        result = response.text.strip().strip('"').strip("'")
        return result[:200]  # Safety cap
    except Exception as e:
        logger.error(f"Gemini summarize error: {e}")
        return user_text.strip()


# ──────────────────────────────────────────────────────────────
# Fallback Intent Analyzer (when Gemini is unavailable)
# ──────────────────────────────────────────────────────────────

# Keywords grouped by intent
_BOOK_KEYWORDS = {
    "book", "repair", "fix", "broken", "not working", "service",
    "install", "maintenance", "leaking", "noise", "issue", "problem",
    "cooling", "heating", "dripping", "damaged", "malfunction",
    "ac", "fridge", "refrigerator", "washing machine", "tv", "television",
    "microwave", "geyser", "water heater", "chimney", "oven", "dishwasher",
    "water purifier", "air conditioner",
}

_WARRANTY_KEYWORDS = {"warranty", "guarantee", "serial", "valid", "expire", "coverage"}

_TRACK_KEYWORDS = {"track", "status", "update", "where", "progress", "check job", "job id"}

_AGENT_KEYWORDS = {"agent", "human", "talk", "speak", "help", "support", "person", "someone", "call"}


def _fallback_intent_analyzer(text):
    """Enhanced keyword matching fallback when Gemini is unavailable."""
    text_lower = text.lower().strip()
    result = {
        "intent": "UNKNOWN",
        "category": None,
        "issue": None,
        "serial": None,
        "job_id": None,
    }

    # Exact number matches (from the menu)
    if text_lower == "1":
        result["intent"] = "BOOK_SERVICE"
        return result
    elif text_lower == "2":
        result["intent"] = "CHECK_WARRANTY"
        return result
    elif text_lower == "3":
        result["intent"] = "TRACK_REQUEST"
        return result
    elif text_lower == "4":
        result["intent"] = "TALK_TO_AGENT"
        return result

    # Check for JOB ID pattern
    import re
    job_match = re.search(r'JOB-\d{8}-\d{4}', text, re.IGNORECASE)
    if job_match:
        result["intent"] = "TRACK_REQUEST"
        result["job_id"] = job_match.group(0).upper()
        return result

    # Score-based matching
    book_score = sum(1 for kw in _BOOK_KEYWORDS if kw in text_lower)
    warranty_score = sum(1 for kw in _WARRANTY_KEYWORDS if kw in text_lower)
    track_score = sum(1 for kw in _TRACK_KEYWORDS if kw in text_lower)
    agent_score = sum(1 for kw in _AGENT_KEYWORDS if kw in text_lower)

    scores = {
        "BOOK_SERVICE": book_score,
        "CHECK_WARRANTY": warranty_score,
        "TRACK_REQUEST": track_score,
        "TALK_TO_AGENT": agent_score,
    }

    best_intent = max(scores, key=scores.get)
    if scores[best_intent] > 0:
        result["intent"] = best_intent

        # Try to extract appliance category for book service
        if best_intent == "BOOK_SERVICE":
            appliances = {
                "ac": "Air Conditioner", "air conditioner": "Air Conditioner",
                "fridge": "Refrigerator", "refrigerator": "Refrigerator",
                "washing machine": "Washing Machine",
                "tv": "Television", "television": "Television",
                "microwave": "Microwave",
                "geyser": "Geyser", "water heater": "Water Heater",
                "chimney": "Chimney", "oven": "Oven",
                "dishwasher": "Dishwasher", "water purifier": "Water Purifier",
            }
            for keyword, name in appliances.items():
                if keyword in text_lower:
                    result["category"] = name
                    break

            # The entire text could be the issue description
            result["issue"] = text.strip()

    return result


# ──────────────────────────────────────────────────────────────
# OTP Generation
# ──────────────────────────────────────────────────────────────

def generate_otp():
    """Generate a random 4-digit OTP for job completion verification."""
    return str(random.randint(1000, 9999))
