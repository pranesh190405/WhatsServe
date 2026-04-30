"""
Start ngrok tunnel for WhatsApp webhook testing.
Run this ALONGSIDE your Django dev server (manage.py runserver).

Usage:
    .venv\\Scripts\\python.exe start_ngrok.py
"""

import os
from dotenv import load_dotenv
from pyngrok import ngrok, conf

load_dotenv()

# Set authtoken from .env
authtoken = os.getenv("NGROK_AUTHTOKEN", "")
if not authtoken or authtoken == "your_authtoken_here":
    print("ERROR: NGROK_AUTHTOKEN not set in .env")
    print("1. Sign up free at https://dashboard.ngrok.com/signup")
    print("2. Copy your authtoken from https://dashboard.ngrok.com/get-started/your-authtoken")
    print("3. Paste it in .env as NGROK_AUTHTOKEN=xxxx")
    exit(1)

conf.get_default().auth_token = authtoken

# Open a tunnel to your Django dev server on port 8000
public_url = ngrok.connect(8000, "http").public_url

webhook_url = f"{public_url}/api/v1/whatsapp/webhook/"

print("=" * 60)
print("  ngrok tunnel is LIVE")
print("=" * 60)
print(f"  Public URL : {public_url}")
print(f"  Webhook URL: {webhook_url}")
print()
print("  Copy the Webhook URL above and paste it into:")
print("     Twilio Console > Messaging > WhatsApp Sandbox")
print("     > 'WHEN A MESSAGE COMES IN' field")
print("     Set method to POST")
print("=" * 60)
print()
print("Press Ctrl+C to stop the tunnel.")

# Keep the process alive
ngrok_process = ngrok.get_ngrok_process()
try:
    ngrok_process.proc.wait()
except KeyboardInterrupt:
    print("\nShutting down ngrok...")
    ngrok.kill()
