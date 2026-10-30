import logging
import smtplib
from email.message import EmailMessage
from typing import Optional, Tuple
from app.core.config import settings
from app.services.brevo_service import send_brevo_email

logger = logging.getLogger("email_service")


def mask_email(email: str) -> str:
    """Mask email for safe audit and debug logging without exposing PII."""
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


def send_smtp_email(
    recipient_email: str,
    subject: str,
    text_body: str,
    html_body: Optional[str] = None,
    recipient_name: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Directly establishes an authentic SMTP connection to the configured mail server,
    negotiates TLS/SSL, authenticates using environment credentials, and sends the message.
    Inspects SMTP response codes and handles specific exceptions safely without logging secrets.
    """
    if not settings.SMTP_HOST:
        logger.warning("SMTP delivery skipped: SMTP_HOST is not configured.")
        return False, "SMTP_HOST is not configured"

    masked_recipient = mask_email(recipient_email)
    sender_name = getattr(settings, "BREVO_SENDER_NAME", None) or "HeartShield Security"
    from_header = f"{sender_name} <{settings.SMTP_FROM_EMAIL}>" if settings.SMTP_FROM_EMAIL else sender_name
    to_header = f"{recipient_name} <{recipient_email}>" if recipient_name else recipient_email

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_header
    msg["To"] = to_header
    msg.set_content(text_body)

    if html_body:
        msg.add_alternative(html_body, subtype="html")

    port = int(settings.SMTP_PORT or 587)

    try:
        logger.info(f"Connecting to SMTP server at {settings.SMTP_HOST}:{port}...")
        if port == 465:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, port, timeout=15)
            server.ehlo()
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, port, timeout=15)
            server.ehlo()
            server.starttls()
            server.ehlo()

        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            logger.info(f"Authenticating with SMTP server as {mask_email(settings.SMTP_USERNAME)}...")
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)

        refused = server.send_message(msg)
        server.quit()

        if refused:
            logger.warning(f"SMTP recipients refused by server for {masked_recipient}: {list(refused.keys())}")
            return False, f"Recipients refused by SMTP server: {list(refused.keys())}"

        logger.info(f"Email successfully delivered and accepted by SMTP server for {masked_recipient} (250 OK)")
        return True, "Email successfully accepted by SMTP server (250 OK)"

    except smtplib.SMTPAuthenticationError as auth_err:
        logger.error(f"SMTP authentication failure ({auth_err.smtp_code}): Username or password not accepted by {settings.SMTP_HOST}")
        return False, f"SMTP authentication failed (code {auth_err.smtp_code})"
    except smtplib.SMTPRecipientsRefused as rec_err:
        logger.error(f"SMTP recipient address refused by server: {masked_recipient}")
        return False, "Recipient address refused by mail server"
    except smtplib.SMTPSenderRefused as send_err:
        logger.error(f"SMTP sender address refused ({send_err.smtp_code})")
        return False, f"Sender address rejected by mail server (code {send_err.smtp_code})"
    except smtplib.SMTPConnectError as conn_err:
        logger.error(f"SMTP connection error: Could not establish connection to {settings.SMTP_HOST}:{port}")
        return False, f"Could not connect to SMTP server: {conn_err}"
    except smtplib.SMTPServerDisconnected as disc_err:
        logger.error(f"SMTP server disconnected unexpectedly during transmission: {disc_err}")
        return False, "SMTP server disconnected unexpectedly"
    except smtplib.SMTPException as smtp_err:
        logger.error(f"SMTP protocol error: {smtp_err}")
        return False, f"SMTP protocol error: {smtp_err}"
    except Exception as exc:
        logger.error(f"Unexpected error during SMTP email dispatch: {type(exc).__name__}")
        return False, f"Unexpected email delivery error: {type(exc).__name__}"


def send_email(
    recipient_email: str,
    subject: str,
    body: str,
    recipient_name: Optional[str] = None
) -> bool:
    """
    Send an email via authenticated SMTP with graceful Brevo API fallback.
    """
    success, detail = send_smtp_email(
        recipient_email=recipient_email,
        subject=subject,
        text_body=body,
        recipient_name=recipient_name
    )

    if not success and getattr(settings, "BREVO_API_KEY", None):
        logger.warning(f"SMTP email dispatch failed ({detail}). Attempting Brevo API fallback...")
        success, brevo_detail = send_brevo_email(
            recipient_email=recipient_email,
            subject=subject,
            body=body,
            recipient_name=recipient_name
        )
        if not success:
            logger.error(f"Brevo email dispatch also failed: {brevo_detail}")

    return success


def send_security_alert_email(
    recipient_email: str,
    raw_token: str,
    role: str = "patient",
    recipient_name: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Dispatches immediate Security Alert email when an account is locked after 6 failed attempts.
    Conforms strictly to Section 2 specifications:
      Subject: Security Alert: Suspicious Login Attempts Detected
      Button: [YES, IT WAS ME]
      Recovery link: verification token URL
    Sends directly via authenticated SMTP (smtp.gmail.com) with Brevo fallback.
    """
    # Resolution: Point verification URL to the configured frontend origin (default: http://localhost:3000)
    frontend_raw = getattr(settings, "FRONTEND_URL", None) or getattr(settings, "FRONTEND_ORIGIN", None) or "http://localhost:3000"
    frontend_url = frontend_raw.strip().rstrip("/")
    if not frontend_url.startswith("http://") and not frontend_url.startswith("https://"):
        frontend_url = f"https://{frontend_url}"
    elif frontend_url.startswith("http://") and not any(h in frontend_url for h in ("localhost", "127.0.0.1", "::1")):
        frontend_url = "https://" + frontend_url[7:]

    unlock_url = f"{frontend_url}/unlock-account?token={raw_token}"
    reset_url = f"{frontend_url}/doctor/forgot-password" if role == "doctor" else f"{frontend_url}/forgot-password"

    subject = "Security Alert: Suspicious Login Attempts Detected"

    text_body = f"""Hello,

We detected multiple unsuccessful login attempts on your HeartShield account.

For your security, login access has been temporarily blocked.

If these attempts were made by you, please click the button below to verify your identity and restore your login access.

[YES, IT WAS ME]
Verification Link: {unlock_url}

If you do not recognize these attempts, do not approve this request. We strongly recommend resetting your password immediately:
Password Reset: {reset_url}

Your account security is our priority.

Regards,
HeartShield Security Team
"""

    display_name = recipient_name or ("Doctor" if role == "doctor" else "User")

    html_body = f"""<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>HeartShield Security Alert</title>
  </head>
  <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #faf7f5; margin: 0; padding: 24px; color: #1f2937;">
    <div style="max-width: 540px; margin: 0 auto; background: #ffffff; border-radius: 16px; border: 1px solid #e5e7eb; padding: 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
      <div style="margin-bottom: 24px;">
        <span style="font-size: 22px; font-weight: 800; color: #b91c1c; letter-spacing: -0.5px;">Heart</span>
        <span style="font-size: 22px; font-weight: 800; color: #1e293b; letter-spacing: -0.5px;">Shield</span>
        <span style="font-size: 11px; background: #fee2e2; color: #991b1b; font-weight: 700; padding: 4px 10px; border-radius: 9999px; margin-left: 8px; text-transform: uppercase; letter-spacing: 0.5px;">Security Alert</span>
      </div>

      <p style="font-size: 15px; line-height: 1.6; margin: 0 0 16px 0;">Hello,</p>

      <p style="font-size: 15px; line-height: 1.6; margin: 0 0 16px 0;">
        We detected multiple unsuccessful login attempts on your HeartShield account.
      </p>

      <div style="background-color: #fef2f2; border-left: 4px solid #ef4444; padding: 12px 16px; border-radius: 4px; margin-bottom: 20px;">
        <p style="margin: 0; font-size: 14px; color: #991b1b; font-weight: 600;">
          For your security, login access has been temporarily blocked.
        </p>
      </div>

      <p style="font-size: 15px; line-height: 1.6; margin: 0 0 24px 0;">
        If these attempts were made by you, please click the button below to verify your identity and restore your login access.
      </p>

      <div style="text-align: center; margin: 28px 0;">
        <a href="{unlock_url}" style="display: inline-block; background-color: #dc2626; color: #ffffff; font-weight: 700; font-size: 14px; text-decoration: none; padding: 12px 28px; border-radius: 8px; box-shadow: 0 2px 4px rgba(220, 38, 38, 0.25);">
          YES, IT WAS ME
        </a>
      </div>

      <p style="font-size: 13px; color: #6b7280; line-height: 1.5; margin: 0 0 20px 0; word-break: break-all;">
        If the button above does not work, copy and paste this verification URL into your browser:<br/>
        <a href="{unlock_url}" style="color: #dc2626; text-decoration: underline;">{unlock_url}</a>
      </p>

      <p style="font-size: 14px; line-height: 1.6; color: #4b5563; margin: 0 0 24px 0;">
        If you do not recognize these attempts, do not approve this request. We strongly recommend resetting your password immediately:<br/>
        <a href="{reset_url}" style="color: #2563eb; font-weight: 600; text-decoration: none;">Reset Password &rarr;</a>
      </p>

      <p style="font-size: 14px; line-height: 1.6; margin: 0 0 8px 0;">
        Your account security is our priority.
      </p>

      <p style="font-size: 14px; font-weight: 600; color: #374151; margin: 0;">
        Regards,<br/>
        HeartShield Security Team
      </p>

      <hr style="border: none; border-top: 1px solid #f3f4f6; margin: 24px 0;" />
      <p style="font-size: 11px; color: #9ca3af; margin: 0; text-align: center;">
        This is an automated security transmission from HeartShield. Please do not reply directly to this email.
      </p>
    </div>
  </body>
</html>
"""

    # 1. Primary delivery: Authenticated SMTP
    success, detail = send_smtp_email(
        recipient_email=recipient_email,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
        recipient_name=display_name
    )

    # 2. Secondary fallback: Brevo API (if SMTP fails or is unconfigured)
    if not success and getattr(settings, "BREVO_API_KEY", None):
        logger.warning(f"SMTP delivery failed ({detail}). Attempting fallback to Brevo API...")
        brevo_success, brevo_detail = send_brevo_email(
            recipient_email=recipient_email,
            subject=subject,
            body=text_body,
            recipient_name=display_name
        )
        if brevo_success:
            return True, "Email accepted via Brevo API fallback"
        else:
            return False, f"SMTP error: {detail}; Brevo fallback error: {brevo_detail}"

    return success, detail
