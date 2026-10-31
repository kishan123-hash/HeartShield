import re
import requests
import logging
from typing import Optional, Tuple
from app.core.config import settings

logger = logging.getLogger("brevo_email_service")

BREVO_BASE_URL = "https://api.brevo.com/v3"
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

# Transactional Email Delivery Status Constants
STATUS_REQUEST_ACCEPTED = "REQUEST_ACCEPTED"
STATUS_DELIVERED = "DELIVERED"
STATUS_DEFERRED = "DEFERRED"
STATUS_BOUNCED = "BOUNCED"
STATUS_BLOCKED = "BLOCKED"
STATUS_DELIVERY_FAILED = "DELIVERY_FAILED"



def mask_email(email: str) -> str:
    """Mask email address for safe audit and debug logging without exposing PII."""
    if not email or "@" not in email:
        return email or "unknown"
    parts = email.split("@", 1)
    username = parts[0]
    domain = parts[1]
    if len(username) <= 2:
        masked_user = f"{username}***"
    else:
        masked_user = f"{username[:2]}***"
    return f"{masked_user}@{domain}"


def validate_recipient_email(email: str) -> Tuple[bool, str]:
    """
    Validates recipient email address syntax and constraints.
    Returns (is_valid: bool, error_message: str).
    """
    if not email or not isinstance(email, str):
        return False, "Recipient email address is required."

    cleaned = email.strip()
    if len(cleaned) > 254:
        return False, "Email address exceeds maximum length of 254 characters."

    if not EMAIL_REGEX.match(cleaned):
        return False, f"Invalid email address format: '{cleaned}'"

    return True, ""


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
    recipient_name: Optional[str] = None,
    html_content: Optional[str] = None,
    text_body: Optional[str] = None,
    html_body: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Send transactional email strictly using the official Brevo Transactional Email REST API.
    Endpoint: POST https://api.brevo.com/v3/smtp/email
    Required headers:
      api-key: BREVO_API_KEY
      Content-Type: application/json
      Accept: application/json

    Does NOT use SMTP, Gmail SMTP, smtp-relay.mailin.fr, or SMTP credentials.
    Returns (success: bool, detail_message: str).
    """
    # 1. Validate Recipient Email
    is_valid, validation_err = validate_recipient_email(recipient_email)
    if not is_valid:
        logger.warning(f"Email delivery rejected due to invalid recipient: {validation_err}")
        return False, validation_err

    clean_recipient = recipient_email.strip().lower()
    masked_recipient = mask_email(clean_recipient)

    # 2. Validate Brevo API Configuration
    api_key = getattr(settings, "BREVO_API_KEY", None)
    if not api_key:
        logger.error("BREVO_API_KEY is not configured in environment settings.")
        return False, "Email service configuration is missing (BREVO_API_KEY)."

    sender_email = (getattr(settings, "BREVO_SENDER_EMAIL", None) or "workingmeet09@gmail.com").strip()
    sender_name = (getattr(settings, "BREVO_SENDER_NAME", None) or "HeartShield").strip()

    # Harmonize body / text_body and html_content / html_body
    resolved_text = (text_body or body or "").strip()
    resolved_html = (html_body or html_content)

    if not resolved_html:
        resolved_html = f"""<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{subject}</title>
  </head>
  <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #faf7f5; margin: 0; padding: 24px; color: #1f2937;">
    <div style="max-width: 540px; margin: 0 auto; background: #ffffff; border-radius: 20px; border: 1px solid #e7e2df; padding: 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.04);">
      <div style="margin-bottom: 24px;">
        <span style="font-size: 22px; font-weight: 900; color: #991b1b; letter-spacing: -0.5px;">Heart</span>
        <span style="font-size: 22px; font-weight: 900; color: #1e293b; letter-spacing: -0.5px;">Shield</span>
        <span style="font-size: 11px; background: #fef2f2; color: #991b1b; font-weight: 700; padding: 4px 10px; border-radius: 9999px; margin-left: 8px;">SECURITY AUTHENTICATION</span>
      </div>
      <div style="font-size: 14px; line-height: 1.6; color: #374151; white-space: pre-line;">
        {resolved_text}
      </div>
      <hr style="border: none; border-top: 1px solid #f3f0ee; margin: 24px 0;" />
      <p style="font-size: 11px; color: #9ca3af; margin: 0;">
        This is an automated transmission from the HeartShield Cardiovascular Intelligence Platform. Please do not reply directly.
      </p>
    </div>
  </body>
</html>"""

    # 3. Construct Official Brevo REST API Request
    url = f"{BREVO_BASE_URL}/smtp/email"
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "sender": {
            "name": sender_name,
            "email": sender_email
        },
        "to": [
            {
                "email": clean_recipient,
                "name": (recipient_name or clean_recipient).strip()
            }
        ],
        "replyTo": {
            "name": sender_name,
            "email": sender_email
        },
        "subject": subject,
        "textContent": resolved_text,
        "htmlContent": resolved_html,
        "tags": ["heartshield-security-alert"]
    }

    # 4. Dispatch HTTPS Request with Timeout Guard
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=12)

        # 5. Parse Brevo API Response
        if response.status_code in (200, 201):
            try:
                res_data = response.json()
                message_id = res_data.get("messageId", "accepted")
            except Exception:
                message_id = "accepted"

            logger.info(f"Brevo email accepted for {masked_recipient} (messageId: {message_id})")
            return True, f"Email accepted by Brevo API (messageId: {message_id})"

        # Handle Brevo API Errors
        err_code = ""
        err_msg = ""
        try:
            err_json = response.json()
            err_code = err_json.get("code", "")
            err_msg = err_json.get("message", "")
        except Exception:
            err_msg = response.text[:200]

        # Categorize specific Brevo error conditions
        status_code = response.status_code
        if status_code == 401:
            detail = "Brevo API authentication failed: invalid or unauthorized API key."
        elif status_code == 403 and ("blacklist" in err_msg.lower() or err_code == "blacklisted_user"):
            detail = f"Recipient {masked_recipient} is blocked/blacklisted in Brevo: {err_msg}"
        elif status_code == 402 or "credit" in err_msg.lower():
            detail = "Brevo account has insufficient transactional email credits."
        elif status_code == 400:
            detail = f"Brevo API rejected email payload: {err_msg or err_code or 'Bad request'}"
        elif status_code == 429:
            detail = "Brevo API rate limit reached. Please retry shortly."
        else:
            detail = f"Brevo email API failed ({status_code}): {err_msg or err_code or response.status_code}"

        logger.error(f"Brevo API failure for {masked_recipient} ({status_code}): {detail}")
        return False, detail

    except requests.Timeout:
        logger.error(f"Brevo API connection timed out for recipient {masked_recipient} (12s threshold)")
        return False, "Brevo email service request timed out after 12 seconds."
    except requests.ConnectionError as conn_err:
        logger.error(f"Brevo API connection error for recipient {masked_recipient}: {type(conn_err).__name__}")
        return False, "Could not establish connection to Brevo API service."
    except Exception as exc:
        logger.error(f"Unexpected exception during Brevo email delivery for {masked_recipient}: {type(exc).__name__}")
        return False, f"Unexpected email delivery error: {type(exc).__name__}"


def dispatch_channel_otp(
    channel: str,
    recipient_email: Optional[str],
    recipient_phone: Optional[str],
    user_name: str,
    otp: str,
    purpose: str = "verification"
) -> Tuple[bool, str]:
    """
    Dispatches a 6-digit OTP code through Email using the official Brevo REST API.
    SMS and WhatsApp OTP delivery have been removed from the platform.
    Returns (success: bool, detail_message: str).
    """
    norm_channel = (channel or "email").strip().lower()

    if norm_channel in ["sms", "whatsapp"]:
        return False, f"OTP delivery via {channel.upper()} has been removed. Only Email OTP is supported."

    if norm_channel != "email":
        return False, f"Unsupported OTP delivery channel: '{channel}'. Only Email OTP is supported."

    if not recipient_email:
        return False, "Recipient email address is required for email delivery."

    # Map purpose to subject, label, and action text
    if purpose == "password_reset":
        purpose_label = "Password Reset"
        purpose_badge = "Password Recovery"
        action_text = "reset your HeartShield account password"
    elif purpose == "doctor_password_reset":
        purpose_label = "Physician Password Recovery"
        purpose_badge = "Physician Recovery"
        action_text = "complete your approved physician password recovery"
    elif purpose == "login":
        purpose_label = "Login Security Verification"
        purpose_badge = "Sign-In Verification"
        action_text = "complete your sign-in verification"
    else:
        purpose_label = "Account Registration Verification"
        purpose_badge = "Account Verification"
        action_text = "verify your new HeartShield account"

    email_subject = f"HeartShield {purpose_label} OTP Code"

    # Plain text body
    email_text_body = f"""Hello {user_name or 'User'},

We received a request to {action_text}.

Your one-time security verification code is:

{otp}

This OTP is strictly valid for 5 minutes.

If you did not initiate this request, please disregard this transmission or notify your administrator immediately.

Best regards,
HeartShield Security Operations
"""

    # Styled HTML card body
    email_html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{email_subject}</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #faf7f5; margin: 0; padding: 24px; color: #1f2937;">
    <div style="max-width: 540px; margin: 0 auto; background: #ffffff; border-radius: 20px; border: 1px solid #e7e2df; padding: 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
        <div style="margin-bottom: 24px;">
            <span style="font-size: 22px; font-weight: 900; color: #991b1b; letter-spacing: -0.5px;">Heart</span>
            <span style="font-size: 22px; font-weight: 900; color: #1e293b; letter-spacing: -0.5px;">Shield</span>
            <span style="font-size: 11px; background: #fef2f2; color: #991b1b; font-weight: 700; padding: 4px 10px; border-radius: 9999px; margin-left: 8px; text-transform: uppercase;">{purpose_badge}</span>
        </div>

        <p style="font-size: 15px; line-height: 1.6; margin: 0 0 16px 0;">Hello {user_name or 'User'},</p>

        <p style="font-size: 14px; line-height: 1.6; color: #4b5563; margin: 0 0 24px 0;">
            We received a request to {action_text}. Please use the following one-time verification code:
        </p>

        <div style="background-color: #faf7f5; border: 1px solid #e7e2df; border-radius: 12px; padding: 20px; text-align: center; margin: 0 0 24px 0;">
            <span style="font-family: 'Courier New', Courier, monospace; font-size: 32px; font-weight: 800; letter-spacing: 8px; color: #991b1b; display: inline-block;">
                {otp}
            </span>
        </div>

        <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 12px 16px; border-radius: 4px; margin: 0 0 24px 0;">
            <p style="margin: 0; font-size: 13px; color: #92400e; font-weight: 600;">
                ⏱️ This code is strictly valid for 5 minutes. Do not share this code with anyone.
            </p>
        </div>

        <p style="font-size: 13px; line-height: 1.5; color: #6b7280; margin: 0 0 24px 0;">
            If you did not initiate this request, your account may be at risk. Please disregard this email or update your password immediately.
        </p>

        <hr style="border: none; border-top: 1px solid #f3f0ee; margin: 24px 0;" />
        <p style="font-size: 11px; color: #9ca3af; margin: 0; text-align: center;">
            This is an automated security transmission from the HeartShield Cardiovascular Intelligence Platform. Please do not reply directly.
        </p>
    </div>
</body>
</html>
"""

    return send_brevo_email(
        recipient_email=recipient_email,
        subject=email_subject,
        body=email_text_body,
        recipient_name=user_name,
        html_content=email_html_body
    )


def query_brevo_delivery_status(message_id: str) -> Tuple[str, dict]:
    """
    Directly queries the official Brevo Transactional Email Event log for a message ID.
    Differentiates:
      - REQUEST_ACCEPTED
      - DELIVERED
      - DEFERRED
      - BOUNCED
      - BLOCKED
      - DELIVERY_FAILED
    Returns (status: str, details: dict).
    """
    if not message_id:
        return STATUS_DELIVERY_FAILED, {"error": "Missing message_id"}

    api_key = getattr(settings, "BREVO_API_KEY", None)
    if not api_key:
        return STATUS_DELIVERY_FAILED, {"error": "BREVO_API_KEY not configured"}

    clean_mid = message_id.strip()
    if not clean_mid.startswith("<"):
        clean_mid = f"<{clean_mid}>"

    headers = {
        "accept": "application/json",
        "api-key": api_key
    }

    try:
        response = requests.get(
            f"{BREVO_BASE_URL}/smtp/statistics/events",
            headers=headers,
            params={"messageId": clean_mid},
            timeout=10
        )
        if response.status_code != 200:
            return STATUS_DELIVERY_FAILED, {"error": f"Brevo API returned {response.status_code}"}

        events = response.json().get("events", [])
        if not events:
            return STATUS_REQUEST_ACCEPTED, {"message": "Queued / Pending indexing in Brevo"}

        event_names = [e.get("event") for e in events]
        if "delivered" in event_names:
            del_ev = next(e for e in events if e.get("event") == "delivered")
            return STATUS_DELIVERED, del_ev
        if any(e in event_names for e in ["hard_bounces", "hardBounces", "soft_bounces", "softBounces"]):
            bounce_ev = next(e for e in events if "bounce" in e.get("event", "").lower())
            return STATUS_BOUNCED, bounce_ev
        if any(e in event_names for e in ["blocked", "spam", "invalid_email"]):
            block_ev = next(e for e in events if e.get("event") in ["blocked", "spam", "invalid_email"])
            return STATUS_BLOCKED, block_ev
        if "deferred" in event_names:
            def_ev = next(e for e in events if e.get("event") == "deferred")
            return STATUS_DEFERRED, def_ev
        if "requests" in event_names:
            return STATUS_REQUEST_ACCEPTED, events[0]

        return STATUS_REQUEST_ACCEPTED, events[0]

    except Exception as exc:
        logger.error(f"Error querying Brevo delivery status for {clean_mid}: {exc}")
        return STATUS_DELIVERY_FAILED, {"error": str(exc)}

