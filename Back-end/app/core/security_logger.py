import logging
import os
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

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
    Security Event Monitoring & Audit Trail.
    Records critical security events without logging passwords, tokens, or PII.
    """

    @staticmethod
    def log_event(
        event_type: str,
        client_ip: str = "unknown",
        user_id: Optional[int] = None,
        role: Optional[str] = None,
        details: str = "",
        status: str = "INFO",
        level: str = "INFO"
    ) -> None:
        user_info = f"user_id={user_id}" if user_id is not None else "user_id=anonymous"
        role_info = f"role={role}" if role is not None else ""
        status_info = f"status={status}"
        message = f"event={event_type} {status_info} ip={client_ip} {user_info} {role_info} details=\"{details}\""

        if level == "WARNING":
            _logger.warning(message)
        elif level == "ERROR":
            _logger.error(message)
        else:
            _logger.info(message)

    @classmethod
    def log_auth_failure(cls, client_ip: str, identifier: str, reason: str = "Invalid credentials", role: Optional[str] = None) -> None:
        masked_id = identifier
        if "@" in identifier:
            parts = identifier.split("@")
            masked_id = f"{parts[0][:2]}***@{parts[1]}"
        cls.log_event("AUTH_FAILURE", client_ip, role=role, details=f"Target: {masked_id}, Reason: {reason}", status="FAILED", level="WARNING")

    @classmethod
    def log_login_success(cls, client_ip: str, user_id: int, role: str) -> None:
        cls.log_event("LOGIN_SUCCESS", client_ip, user_id=user_id, role=role, details="Successful authentication", status="SUCCESS", level="INFO")

    @classmethod
    def log_account_locked(cls, client_ip: str, user_id: int, role: str, attempt_count: int) -> None:
        cls.log_event("ACCOUNT_LOCKED", client_ip, user_id=user_id, role=role, details=f"Locked after {attempt_count} consecutive failed attempts", status="BLOCKED", level="WARNING")

    @classmethod
    def log_security_email_sent(cls, client_ip: str, user_id: int, role: str, email: str, details: Optional[str] = None) -> None:
        masked_email = email
        if "@" in email:
            parts = email.split("@")
            masked_email = f"{parts[0][:2]}***@{parts[1]}"
        event_details = details or f"Unlock notification dispatched to {masked_email}"
        cls.log_event("SECURITY_EMAIL_SENT", client_ip, user_id=user_id, role=role, details=event_details, status="SENT", level="INFO")

    @classmethod
    def log_security_email_failed(cls, client_ip: str, user_id: int, role: str, email: str, reason: str) -> None:
        masked_email = email
        if "@" in email:
            parts = email.split("@")
            masked_email = f"{parts[0][:2]}***@{parts[1]}"
        cls.log_event("SECURITY_EMAIL_FAILED", client_ip, user_id=user_id, role=role, details=f"Failed dispatching to {masked_email}: {reason}", status="FAILED", level="ERROR")

    @classmethod
    def log_account_unlocked(cls, client_ip: str, user_id: int, role: str, method: str = "email_token") -> None:
        cls.log_event("ACCOUNT_UNLOCKED", client_ip, user_id=user_id, role=role, details=f"Account unlocked via {method}", status="SUCCESS", level="INFO")

    @classmethod
    def log_password_reset(cls, client_ip: str, user_id: int, role: str) -> None:
        cls.log_event("PASSWORD_RESET", client_ip, user_id=user_id, role=role, details="Password reset completed; prior sessions revoked", status="SUCCESS", level="INFO")

    @classmethod
    def log_suspicious_ip(cls, client_ip: str, reason: str) -> None:
        cls.log_event("SUSPICIOUS_IP_ACTIVITY", client_ip, details=reason, status="RESTRICTED", level="WARNING")

    @classmethod
    def log_session_invalidation(cls, client_ip: str, user_id: Optional[int], reason: str) -> None:
        cls.log_event("SESSION_INVALIDATED", client_ip, user_id=user_id, details=reason, status="REVOKED", level="INFO")

    @classmethod
    def log_otp_failure(cls, client_ip: str, email: str, reason: str) -> None:
        parts = email.split("@") if "@" in email else [email, ""]
        masked_email = f"{parts[0][:2]}***@{parts[1]}" if len(parts) > 1 else email
        cls.log_event("OTP_FAILURE", client_ip, details=f"Email: {masked_email}, Reason: {reason}", status="FAILED", level="WARNING")

    @classmethod
    def log_rate_limit(cls, client_ip: str, endpoint: str) -> None:
        cls.log_event("RATE_LIMIT_EXCEEDED", client_ip, details=f"Path: {endpoint}", status="BLOCKED", level="WARNING")

    @classmethod
    def log_unauthorized_access(cls, client_ip: str, user_id: Optional[int], endpoint: str, reason: str) -> None:
        cls.log_event("UNAUTHORIZED_ACCESS_ATTEMPT", client_ip, user_id=user_id, details=f"Path: {endpoint}, Reason: {reason}", status="DENIED", level="WARNING")

    @classmethod
    def log_token_revocation(cls, client_ip: str, user_id: Optional[int]) -> None:
        cls.log_event("TOKEN_REVOCATION", client_ip, user_id=user_id, details="User successfully logged out; token added to revocation blocklist", status="REVOKED", level="INFO")

    @classmethod
    def log_file_violation(cls, client_ip: str, user_id: Optional[int], filename: str, reason: str) -> None:
        cls.log_event("FILE_VALIDATION_VIOLATION", client_ip, user_id=user_id, details=f"Filename: {filename}, Reason: {reason}", status="REJECTED", level="WARNING")


security_logger = SecurityLogger()


def record_security_audit(
    db: Optional[Session],
    event_type: str,
    client_ip: str,
    user_id: Optional[int] = None,
    role: Optional[str] = None,
    status: str = "SUCCESS",
    details: str = "",
    level: str = "INFO"
) -> None:
    """
    Centralized security audit recorder.
    Writes to permanent security log file and persists to database activity_logs without storing credentials.
    """
    # 1. Log to file
    security_logger.log_event(
        event_type=event_type,
        client_ip=client_ip,
        user_id=user_id,
        role=role,
        details=details,
        status=status,
        level=level
    )

    # 2. Persist to ActivityLog in database if db session provided
    if db:
        try:
            from app.models.activity_log import ActivityLog
            act = ActivityLog(
                user_id=user_id,
                action=f"{event_type}:{status}",
                entity_type="SECURITY_AUDIT",
                entity_id=user_id,
                ip_address=client_ip[:45] if client_ip else "127.0.0.1"
            )
            db.add(act)
            db.commit()
        except Exception as db_err:
            db.rollback()
            _logger.error(f"Failed to persist security activity log to DB: {db_err}")
