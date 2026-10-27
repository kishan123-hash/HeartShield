import re
import requests
import logging
from app.core.config import settings

logger = logging.getLogger("brevo")

BREVO_BASE_URL = "https://api.brevo.com/v3"


def format_phone_e164(phone: str) -> str:
    """
    Standardize a phone number for international delivery.
    Preserves '+' prefix or adds '+91' if 10 plain digits are provided.
    """
    if not phone:
        return ""
    cleaned = re.sub(r"[^\d+]", "", phone.strip())
    if cleaned.startswith("+"):
        return cleaned
    if len(cleaned) == 10:
        return f"+91{cleaned}"
    return f"+{cleaned}"


def send_brevo_email(
    recipient_email: str,
    subject: str,
    body: str,
    recipient_name: str | None = None
) -> tuple[bool, str]:
    """
    Send transactional email using Brevo's official HTTPS API.
    """
    if not settings.BREVO_API_KEY:
        logger.error("BREVO_API_KEY is not configured in settings.")
        return False, "Email service configuration is missing (BREVO_API_KEY)."

    url = f"{BREVO_BASE_URL}/smtp/email"
    headers = {
        "api-key": settings.BREVO_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    html_content = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8" />
      </head>
      <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #faf7f5; margin: 0; padding: 24px;">
        <div style="max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 20px; border: 1px solid #e7e2df; padding: 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
          <div style="margin-bottom: 24px;">
            <span style="font-size: 20px; font-weight: 900; color: #991b1b; letter-spacing: -0.5px;">Heart</span>
            <span style="font-size: 20px; font-weight: 900; color: #7f1d1d; letter-spacing: -0.5px;">Shield</span>
            <span style="font-size: 11px; background: #fef2f2; color: #991b1b; font-weight: 700; padding: 3px 8px; border-radius: 9999px; margin-left: 8px;">SECURITY AUTHENTICATION</span>
          </div>
          <div style="font-size: 14px; line-height: 1.6; color: #374151; white-space: pre-line;">
            {body}
          </div>
          <hr style="border: none; border-top: 1px solid #f3f0ee; margin: 24px 0;" />
          <p style="font-size: 11px; color: #9ca3af; margin: 0;">
            This is an automated security transmission from the HeartShield Cardiovascular Intelligence Platform. Please do not reply directly.
          </p>
        </div>
      </body>
    </html>
    """

    payload = {
        "sender": {
            "name": settings.BREVO_SENDER_NAME or "HeartShield",
            "email": settings.BREVO_SENDER_EMAIL or "workingmeet09@gmail.com"
        },
        "to": [
            {
                "email": recipient_email,
                "name": recipient_name or recipient_email
            }
        ],
        "subject": subject,
        "textContent": body,
        "htmlContent": html_content
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=12)
        if response.status_code in (200, 201):
            return True, "Email sent successfully"
        else:
            try:
                err_data = response.json()
                msg = err_data.get("message") or err_data.get("code") or response.text
            except Exception:
                msg = response.text
            logger.error(f"Brevo email API failed with status {response.status_code}: {msg}")
            return False, f"Email delivery failed: {msg}"
    except Exception as e:
        logger.error(f"Brevo email connection error: {e}")
        return False, f"Email service unreachable: {str(e)}"


def dispatch_channel_otp(
    channel: str,
    recipient_email: str | None,
    recipient_phone: str | None,
    user_name: str,
    otp: str,
    purpose: str = "verification"
) -> tuple[bool, str]:
    """
    Dispatches an OTP through Email.
    SMS and WhatsApp OTP delivery have been removed from the platform.
    Returns (success: bool, detail_message: str).
    """
    norm_channel = (channel or "email").strip().lower()

    if norm_channel in ["sms", "whatsapp"]:
        return False, f"OTP delivery via {channel.upper()} has been removed. Only Email OTP is supported."

    if norm_channel != "email":
        return False, f"Unsupported OTP delivery channel: '{channel}'. Only Email OTP is supported."

    if purpose == "password_reset":
        purpose_label = "Password Reset"
        action_text = "reset your HeartShield account password"
    elif purpose == "doctor_password_reset":
        purpose_label = "Physician Password Recovery"
        action_text = "complete your approved physician password recovery"
    else:
        purpose_label = "Account Registration Verification"
        action_text = "verify your new HeartShield account"

    # Email content
    email_subject = f"HeartShield {purpose_label} OTP Code"
    email_body = f"""Hello {user_name or 'User'},

We received a request to {action_text}.

Your one-time security verification code is:

{otp}

This OTP is strictly valid for 5 minutes.

If you did not initiate this request, please disregard this transmission or notify your administrator immediately.

Best regards,
HeartShield Security Operations
"""

    if not recipient_email:
        return False, "Recipient email address is required for email delivery."

    return send_brevo_email(
        recipient_email=recipient_email,
        subject=email_subject,
        body=email_body,
        recipient_name=user_name
    )
