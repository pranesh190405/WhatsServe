import os
import json
import logging
from openai import OpenAI
from twilio.rest import Client

logger = logging.getLogger(__name__)

# Twilio Configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "+14155238886")

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
_openai_client = None

def get_openai_client():
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and api_key != "your-openai-api-key-here":
            _openai_client = OpenAI(api_key=api_key)
    return _openai_client

def analyze_intent(user_text):
    """
    Analyzes the user's text using OpenAI to determine their intent.
    Returns a dict like:
    {
        "intent": "BOOK_SERVICE" | "CHECK_WARRANTY" | "TRACK_REQUEST" | "TALK_TO_AGENT" | "UNKNOWN",
        "category": "appliance type if found" | null,
        "serial": "serial number if found" | null,
        "job_id": "job id if found" | null
    }
    """
    client = get_openai_client()
    
    # Fallback if OpenAI is not configured
    if not client:
        logger.warning("OpenAI client not configured. Falling back to keyword matching.")
        return _fallback_intent_analyzer(user_text)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a smart router for an electronics after-sales service WhatsApp bot. "
                        "Determine the user's intent and extract any relevant entities. "
                        "Valid intents are: BOOK_SERVICE, CHECK_WARRANTY, TRACK_REQUEST, TALK_TO_AGENT, UNKNOWN. "
                        "Return ONLY valid JSON in this format: "
                        "{\"intent\": \"INTENT_NAME\", \"category\": \"appliance type if applicable\", \"serial\": \"serial number if applicable\", \"job_id\": \"job id if applicable\"}"
                    )
                },
                {"role": "user", "content": user_text}
            ],
            response_format={ "type": "json_object" },
            temperature=0.0,
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
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
