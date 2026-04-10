import os

SIMULATION = os.getenv("SIMULATION_MODE") == "true"

def send_whatsapp(to, message):
    if SIMULATION:
        print(f"[SIMULATED WhatsApp] → {to}: {message}")
        return "simulated"
    else:
        # real API
        pass