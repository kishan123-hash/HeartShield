import smtplib
from email.message import EmailMessage

from app.core.config import settings


def send_email(
    recipient_email: str,
    subject: str,
    body: str
) -> bool:
    """
    Send an email using the configured SMTP server.
    """

    message = EmailMessage()

    message["Subject"] = subject
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = recipient_email

    message.set_content(body)

    try:

        with smtplib.SMTP(
            settings.SMTP_HOST,
            settings.SMTP_PORT
        ) as server:

            server.starttls()

            server.login(
                settings.SMTP_USERNAME,
                settings.SMTP_PASSWORD
            )

            server.send_message(message)

        return True

    except Exception as e:

        print(f"Email sending failed: {e}")

        return False