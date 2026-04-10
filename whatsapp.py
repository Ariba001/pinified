import os

SIMULATION = os.getenv("SIMULATION_MODE") == "true"

def send_whatsapp(to, message):
    if SIMULATION:
        print(f"[SIMULATED WhatsApp] → {to}: {message}")
        return "simulated"
    else:
        # real API
        pass


from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

client = Client(ACCOUNT_SID, AUTH_TOKEN)


# def send_whatsapp(to, message):
#     '''
#     Sends WhatsApp message using Twilio API
#     '''

#     try:
#         msg = client.messages.create(
#             from_='whatsapp:+14155238886',
#             body=message,
#             to=f'whatsapp:{to}'
#         )
#         return msg.sid

#     except Exception as e:
#         print("WhatsApp Error:", e)
#         return None
# """