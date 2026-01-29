import datetime

# --- CONFIGURATION ---
# If you have a Twilio account, fill these in later.
# For now, we will use 'MOCK' mode.
SMS_MODE = "MOCK"  # Options: "MOCK" or "TWILIO"
TWILIO_SID = "your_sid_here"
TWILIO_AUTH_TOKEN = "your_token_here"
TWILIO_PHONE = "+1234567890"

def send_sms_nudge(citizen_name, score, failure_prob):
    """
    Decides whether to send a real SMS or just log it.
    """
    message_body = (
        f"⚠️ AADHAAR ALERT: {citizen_name}, your biometric health score "
        f"has dropped to {score}/100. Risk of failure: {int(failure_prob * 100)}%. "
        f"Please visit your nearest center immediately to update biometrics."
    )

    if SMS_MODE == "TWILIO":
        # real_send_twilio(message_body) # Uncomment this if you add keys later
        pass
    else:
        # MOCK MODE: specific visual print for the terminal
        print("\n" + "="*50)
        print("🚀 [SMS GATEWAY] MESSAGE DISPATCHED")
        print(f"TO:   {citizen_name} (+91 XXXXX XXXXX)")
        print(f"MSG:  {message_body}")
        print(f"TIME: {datetime.datetime.now()}")
        print("="*50 + "\n")
        
    return True