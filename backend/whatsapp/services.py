import os
import json
import logging
from google import genai
from google.genai import types
from twilio.rest import Client

logger = logging.getLogger(__name__)

# Twilio Configuration
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

# Initialize client lazily
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
    Returns a dict like:
    {
        "intent": "BOOK_SERVICE" | "CHECK_WARRANTY" | "TRACK_REQUEST" | "TALK_TO_AGENT" | "UNKNOWN",
        "category": "appliance type if found" | null,
        "serial": "serial number if found" | null,
        "job_id": "job id if found" | null
    }
    """
    client = get_gemini_client()
    
    # Fallback if Gemini is not configured
    if not client:
        logger.warning("Gemini client not configured. Falling back to keyword matching.")
        return _fallback_intent_analyzer(user_text)

    prompt = f"""
    You are a smart router for an electronics after-sales service WhatsApp bot.
    Determine the user's intent and extract any relevant entities.
    Valid intents are: BOOK_SERVICE, CHECK_WARRANTY, TRACK_REQUEST, TALK_TO_AGENT, UNKNOWN.
    
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
                        "serial": {"type": "STRING", "nullable": True},
                        "job_id": {"type": "STRING", "nullable": True}
                    },
                    "required": ["intent"]
                },
                temperature=0.0
            )
        )
        content = response.text
        return json.loads(content)
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return _fallback_intent_analyzer(user_text)

def _fallback_intent_analyzer(text):
    """Basic keyword matching if GPT fails or is not configured."""
    text_lower = text.lower().strip()
    result = {
        "intent": "UNKNOWN",
        "category": None,
        "serial": None,
        "job_id": None
    }
    
    if text_lower == "1" or "book" in text_lower or "repair" in text_lower:
        result["intent"] = "BOOK_SERVICE"
    elif text_lower == "2" or "warranty" in text_lower:
        result["intent"] = "CHECK_WARRANTY"
    elif text_lower == "3" or "track" in text_lower or "status" in text_lower:
        result["intent"] = "TRACK_REQUEST"
    elif text_lower == "4" or "agent" in text_lower or "talk" in text_lower or "human" in text_lower:
        result["intent"] = "TALK_TO_AGENT"
        
    return result
