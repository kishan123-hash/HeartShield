import logging
from datetime import datetime
from typing import Optional, Tuple
from app.core.config import settings
from app.services.brevo_service import (
    send_brevo_email,
    mask_email,
    validate_recipient_email
)

logger = logging.getLogger("email_service")


def send_email(
    recipient_email: str,
    subject: str,
    body: str,
    recipient_name: Optional[str] = None
) -> bool:
    """
    Send a transactional email using the official Brevo REST API.
    Replaces legacy SMTP delivery entirely.
    """
    success, detail = send_brevo_email(
        recipient_email=recipient_email,
        subject=subject,
        body=body,
        recipient_name=recipient_name
    )
    if not success:
        logger.error(f"Email dispatch via Brevo REST API failed: {detail}")
    return success


def send_smtp_email(
    recipient_email: str,
    subject: str,
    text_body: str,
    html_body: Optional[str] = None,
    recipient_name: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Compatibility shim for tests: Routes transactional emails directly to the official Brevo REST API.
    Raw SMTP socket transmission (smtp.gmail.com / mailin) has been removed.
    """
    return send_brevo_email(
        recipient_email=recipient_email,
        subject=subject,
        body=text_body,
        recipient_name=recipient_name,
        html_content=html_body,
        text_body=text_body,
        html_body=html_body
    )


def send_security_alert_email(
    recipient_email: str,
    raw_token: str,
    role: str = "patient",
    recipient_name: Optional[str] = None,
    reset_token: Optional[str] = None,
    ip_address: Optional[str] = None,
    timestamp: Optional[str] = None,
    activity_type: Optional[str] = None,
    subject: Optional[str] = None,
    **kwargs
) -> Tuple[bool, str]:
    """
    Dispatches immediate Security Alert email when an account is locked after failed login attempts.
    Uses strictly the official Brevo Transactional Email REST API.
    
    Email Specifications:
      Subject: Security Alert: Suspicious Login Activity Detected – HeartShield
      Content:
        - Registered User Name greeting
        - Notification of multiple failed login attempts & account lockout
        - Security Activity Details (Activity type, timestamp, IP address)
        - Question: Do you recognize this login activity?
        - Action Button 1: [YES, IT WAS ME] -> identity verification & unlock flow
        - Action Button 2: [NO, IT WAS NOT ME] -> email OTP verification & secure password reset flow
    """
    if not recipient_email:
        return False, "Recipient email address is required."

    frontend_raw = (
        getattr(settings, "FRONTEND_URL", None)
        or getattr(settings, "FRONTEND_ORIGIN", None)
        or "http://localhost:3000"
    )

    frontend_url = frontend_raw.strip().rstrip("/")
    if not frontend_url.startswith(("http://", "https://")):
        frontend_url = f"https://{frontend_url}"
    elif frontend_url.startswith("http://") and not any(
        host in frontend_url
        for host in ("localhost", "127.0.0.1", "::1")
    ):
        frontend_url = "https://" + frontend_url[7:]

    active_reset_token = reset_token or raw_token
    unlock_url = f"{frontend_url}/unlock-account?token={raw_token}"
    reset_url = f"{frontend_url}/unlock-account?token={active_reset_token}&action=reset"

    email_subject = subject or "Security Alert: Suspicious Login Activity Detected – HeartShield"
    display_name = recipient_name or ("Doctor" if role == "doctor" else "User")
    resolved_time = timestamp or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    resolved_ip = ip_address or "Not Available"
    resolved_activity = activity_type or "Multiple Consecutive Failed Login Attempts"

    doctor_extra_text = (
        f"\n(For physician administrative reset portal, visit: {frontend_url}/doctor/forgot-password)\n"
        if role == "doctor"
        else ""
    )

    text_body = f"""Hello {display_name},

We detected multiple consecutive unsuccessful login attempts on your HeartShield account.

For your security, login access to your account has been temporarily locked to protect your data and prevent unauthorized access.

Security Activity Details:
- Activity: {resolved_activity}
- Time: {resolved_time}
- IP Address: {resolved_ip}

Do you recognize this login activity?

If these attempts were made by you, please verify your identity using your current password to restore your login access:
[YES, IT WAS ME]
Verification Link: {unlock_url}

If you did not make these attempts, please secure your account immediately:
[NO, IT WAS NOT ME]
Secure & Reset Link: {reset_url}
{doctor_extra_text}
Your account security is our highest priority.

Regards,
HeartShield Security Team
"""

    html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>HeartShield Security Alert</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #faf7f5; margin: 0; padding: 24px; color: #1f2937;">
    <div style="max-width: 560px; margin: 0 auto; background: #ffffff; border-radius: 16px; border: 1px solid #e5e7eb; padding: 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
        <div style="margin-bottom: 24px;">
            <span style="font-size: 22px; font-weight: 800; color: #b91c1c; letter-spacing: -0.5px;">Heart</span>
            <span style="font-size: 22px; font-weight: 800; color: #1e293b; letter-spacing: -0.5px;">Shield</span>
            <span style="font-size: 11px; background: #fee2e2; color: #991b1b; font-weight: 700; padding: 4px 10px; border-radius: 9999px; margin-left: 8px; text-transform: uppercase; letter-spacing: 0.5px;">Security Alert</span>
        </div>

        <p style="font-size: 15px; line-height: 1.6; margin: 0 0 16px 0;">Hello {display_name},</p>

        <p style="font-size: 15px; line-height: 1.6; margin: 0 0 16px 0;">
            We detected multiple consecutive unsuccessful login attempts on your HeartShield account.
        </p>

        <div style="background-color: #fef2f2; border-left: 4px solid #ef4444; padding: 14px 16px; border-radius: 4px; margin-bottom: 20px;">
            <p style="margin: 0; font-size: 14px; color: #991b1b; font-weight: 600;">
                For your security, login access to your account has been temporarily locked to protect your data and prevent unauthorized access.
            </p>
        </div>

        <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin: 20px 0;">
            <p style="margin: 0 0 10px 0; font-size: 12px; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.5px;">Security Activity Details</p>
            <table role="presentation" border="0" cellpadding="0" cellspacing="0" style="width: 100%; font-size: 13px; color: #334155;">
                <tr>
                    <td style="padding: 4px 0; font-weight: 600; width: 110px; color: #64748b;">Activity:</td>
                    <td style="padding: 4px 0; font-weight: 600; color: #b91c1c;">{resolved_activity}</td>
                </tr>
                <tr>
                    <td style="padding: 4px 0; font-weight: 600; color: #64748b;">Time:</td>
                    <td style="padding: 4px 0; color: #1e293b;">{resolved_time}</td>
                </tr>
                <tr>
                    <td style="padding: 4px 0; font-weight: 600; color: #64748b;">IP Address:</td>
                    <td style="padding: 4px 0; font-family: monospace; color: #1e293b;">{resolved_ip}</td>
                </tr>
            </table>
        </div>

        <p style="font-size: 14px; font-weight: 700; color: #1e293b; margin: 24px 0 12px 0; text-align: center;">
            Do you recognize this login activity?
        </p>

        <div style="margin: 20px 0; text-align: center;">
            <table role="presentation" border="0" cellpadding="0" cellspacing="0" style="margin: 0 auto;">
                <tr>
                    <td style="padding: 0 8px 12px 8px;">
                        <a href="{unlock_url}" style="display: inline-block; background-color: #059669; color: #ffffff; font-size: 14px; font-weight: 700; text-decoration: none; padding: 12px 24px; border-radius: 8px; box-shadow: 0 2px 4px rgba(5, 150, 105, 0.25);">
                            YES, IT WAS ME
                        </a>
                    </td>
                    <td style="padding: 0 8px 12px 8px;">
                        <a href="{reset_url}" style="display: inline-block; background-color: #dc2626; color: #ffffff; font-size: 14px; font-weight: 700; text-decoration: none; padding: 12px 24px; border-radius: 8px; box-shadow: 0 2px 4px rgba(220, 38, 38, 0.25);">
                            NO, IT WAS NOT ME
                        </a>
                    </td>
                </tr>
            </table>
        </div>

        <div style="background-color: #f9fafb; border-radius: 8px; padding: 16px; margin: 24px 0; font-size: 12px; color: #4b5563; line-height: 1.6;">
            <p style="margin: 0 0 8px 0;"><strong>What do these actions do?</strong></p>
            <p style="margin: 0 0 6px 0;">• <strong>YES, IT WAS ME:</strong> Verify your identity using your current password to unlock your account immediately.</p>
            <p style="margin: 0;">• <strong>NO, IT WAS NOT ME:</strong> Report suspicious activity, verify via email code (OTP), and securely reset your password to protect your account.</p>
        </div>

        <p style="font-size: 12px; color: #6b7280; line-height: 1.5; margin: 0 0 6px 0;">
            If the buttons above do not open directly, copy and paste either link below into your browser:
        </p>
        <p style="font-size: 11px; color: #4b5563; margin: 0 0 4px 0;"><strong>Verify &amp; Unlock:</strong></p>
        <div style="font-family: monospace; font-size: 11px; color: #1f2937; background: #f3f4f6; border: 1px solid #e5e7eb; border-radius: 4px; padding: 8px 10px; margin: 0 0 10px 0; word-break: break-all;">
            {unlock_url}
        </div>
        <p style="font-size: 11px; color: #4b5563; margin: 0 0 4px 0;"><strong>Secure Account &amp; Reset:</strong></p>
        <div style="font-family: monospace; font-size: 11px; color: #1f2937; background: #f3f4f6; border: 1px solid #e5e7eb; border-radius: 4px; padding: 8px 10px; margin: 0 0 20px 0; word-break: break-all;">
            {reset_url}
        </div>

        <p style="font-size: 14px; line-height: 1.6; margin: 0 0 8px 0;">
            Your account security is our highest priority.
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

    # Deliver directly and exclusively through the official Brevo Transactional Email REST API
    return send_brevo_email(
        recipient_email=recipient_email,
        subject=email_subject,
        body=text_body,
        recipient_name=display_name,
        html_content=html_body,
        text_body=text_body,
        html_body=html_body
    )


def send_password_change_confirmation_email(
    recipient_email: str,
    recipient_name: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Sends a security confirmation email after a successful password update.
    Uses strictly the official Brevo Transactional Email REST API.
    """
    if not recipient_email:
        return False, "Recipient email address is required."

    display_name = recipient_name or "HeartShield User"
    subject = "HeartShield Security Alert: Password Changed"

    text_body = f"""Hello {display_name},

This email confirms that the password for your HeartShield account ({recipient_email}) was successfully changed.

If you made this change, your account is now secured and you may log in with your new credentials.

If you did NOT authorize this change, please contact HeartShield Security immediately.

Regards,
HeartShield Security Team
"""

    html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>HeartShield Password Changed</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #faf7f5; margin: 0; padding: 24px; color: #1f2937;">
    <div style="max-width: 560px; margin: 0 auto; background: #ffffff; border-radius: 16px; border: 1px solid #e5e7eb; padding: 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
        <div style="margin-bottom: 24px;">
            <span style="font-size: 22px; font-weight: 800; color: #b91c1c; letter-spacing: -0.5px;">Heart</span>
            <span style="font-size: 22px; font-weight: 800; color: #1e293b; letter-spacing: -0.5px;">Shield</span>
            <span style="font-size: 11px; background: #dcfce7; color: #166534; font-weight: 700; padding: 4px 10px; border-radius: 9999px; margin-left: 8px; text-transform: uppercase; letter-spacing: 0.5px;">Security Update</span>
        </div>

        <p style="font-size: 15px; line-height: 1.6; margin: 0 0 16px 0;">Hello {display_name},</p>

        <p style="font-size: 15px; line-height: 1.6; margin: 0 0 16px 0;">
            This email confirms that the password for your HeartShield account (<strong style="color: #111827;">{recipient_email}</strong>) has been successfully changed.
        </p>

        <div style="background-color: #f0fdf4; border-left: 4px solid #22c55e; padding: 14px 16px; border-radius: 4px; margin-bottom: 24px;">
            <p style="margin: 0; font-size: 14px; color: #15803d; font-weight: 600;">
                Your account is unlocked and protected. You may now sign in using your new credentials.
            </p>
        </div>

        <p style="font-size: 13px; color: #4b5563; line-height: 1.6; margin: 0 0 20px 0;">
            If you did not initiate this change, your account may be compromised. Please contact support immediately.
        </p>

        <p style="font-size: 14px; font-weight: 600; color: #374151; margin: 0;">
            Regards,<br/>
            HeartShield Security Team
        </p>
    </div>
</body>
</html>
"""

    return send_brevo_email(
        recipient_email=recipient_email,
        subject=subject,
        body=text_body,
        recipient_name=display_name,
        html_content=html_body,
        text_body=text_body,
        html_body=html_body
    )
