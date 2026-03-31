import random
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

def generate_otp(length=6):
    """Generate a random OTP."""
    return "".join(random.choices("0123456789", k=length))

def send_otp_sms(phone_number, otp):
    """Send OTP via Twilio SMS."""
    if not all(
        [
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN,
            settings.TWILIO_PHONE_NUMBER,
        ]
    ):
        logger.error("Twilio settings are incomplete; OTP SMS cannot be sent.")
        return False, "Twilio settings are incomplete."

    try:
        from twilio.rest import Client

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=f"Your Employee Portal OTP is: {otp}. It is valid for 5 minutes.",
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone_number,
        )
        return True, message.sid
    except ImportError as exc:
        logger.error("Twilio dependency is not installed: %s", exc)
        return False, "Twilio dependency is not installed."
    except Exception as exc:
        logger.error("Failed to send OTP to %s: %s", phone_number, exc)
        return False, str(exc)
