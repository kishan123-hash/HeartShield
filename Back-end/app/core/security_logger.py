import logging
import os
from datetime import datetime, timezone
from typing import Optional

# Set up security logger to write to both security_events.log and system logger
log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
log_file = os.path.join(log_dir, "security_events.log")

_logger = logging.getLogger("heartshield_security")
_logger.setLevel(logging.INFO)

# File handler for permanent security audit trail
if not any(isinstance(h, logging.FileHandler) and h.baseFilename == log_file for h in _logger.handlers):
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [SECURITY_AUDIT] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    _logger.addHandler(file_handler)


class SecurityLogger:
    """
    Layer 5 Security Event Monitoring & Audit Trail.
    Records critical security events without logging passwords, tokens, or PII.
    """

    @staticmethod
    def log_event(
        event_type: str,
        client_ip: str = "unknown",
        user_id: Optional[int] = None,
        details: str = "",
        level: str = "INFO"
    ) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        user_info = f"user_id={user_id}" if user_id is not None else "user_id=anonymous"
        message = f"event={event_type} ip={client_ip} {user_info} details=\"{details}\""
        
        if level == "WARNING":
            _logger.warning(message)
        elif level == "ERROR":
            _logger.error(message)
        else:
            _logger.info(message)

    @classmethod
    def log_auth_failure(cls, client_ip: str, identifier: str, reason: str = "Invalid credentials") -> None:
        # Sanitize identifier (mask email prefix if email)
        masked_id = identifier
        if "@" in identifier:
            parts = identifier.split("@")
            masked_id = f"{parts[0][:2]}***@{parts[1]}"
        cls.log_event("AUTH_FAILURE", client_ip, details=f"Target: {masked_id}, Reason: {reason}", level="WARNING")

    @classmethod
    def log_otp_failure(cls, client_ip: str, email: str, reason: str) -> None:
        parts = email.split("@") if "@" in email else [email, ""]
        masked_email = f"{parts[0][:2]}***@{parts[1]}" if len(parts) > 1 else email
        cls.log_event("OTP_FAILURE", client_ip, details=f"Email: {masked_email}, Reason: {reason}", level="WARNING")

    @classmethod
    def log_rate_limit(cls, client_ip: str, endpoint: str) -> None:
        cls.log_event("RATE_LIMIT_EXCEEDED", client_ip, details=f"Path: {endpoint}", level="WARNING")

    @classmethod
    def log_unauthorized_access(cls, client_ip: str, user_id: Optional[int], endpoint: str, reason: str) -> None:
        cls.log_event("UNAUTHORIZED_ACCESS_ATTEMPT", client_ip, user_id, details=f"Path: {endpoint}, Reason: {reason}", level="WARNING")

    @classmethod
    def log_token_revocation(cls, client_ip: str, user_id: Optional[int]) -> None:
        cls.log_event("TOKEN_REVOCATION", client_ip, user_id, details="User successfully logged out; token added to revocation blocklist", level="INFO")

    @classmethod
    def log_file_violation(cls, client_ip: str, user_id: Optional[int], filename: str, reason: str) -> None:
        cls.log_event("FILE_VALIDATION_VIOLATION", client_ip, user_id, details=f"Filename: {filename}, Reason: {reason}", level="WARNING")


security_logger = SecurityLogger()
