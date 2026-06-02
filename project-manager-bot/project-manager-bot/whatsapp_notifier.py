import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

def send_whatsapp(to_number, message):
    try:
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        from_number = os.getenv("TWILIO_WHATSAPP_FROM")

        client = Client(account_sid, auth_token)
        msg = client.messages.create(
            body=message,
            from_=from_number,
            to=f"whatsapp:{to_number}" if not to_number.startswith("whatsapp:") else to_number
        )
        print(f"WhatsApp sent! SID: {msg.sid}")
        return True
    except Exception as e:
        print(f"WhatsApp error: {e}")
        return False
