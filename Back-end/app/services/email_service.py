import logging
from app.services.brevo_service import send_brevo_email

logger = logging.getLogger("email_service")


def send_email(
    recipient_email: str,
    subject: str,
    body: str
) -> bool:
    """
    Send an email using Brevo's official HTTPS transactional email API.
    Replaces legacy SMTP in adherence to strict security guidelines.
    """
    success, detail = send_brevo_email(
        recipient_email=recipient_email,
        subject=subject,
        body=body
    )
    if not success:
        logger.error(f"Brevo email dispatch failed: {detail}")
    return success
