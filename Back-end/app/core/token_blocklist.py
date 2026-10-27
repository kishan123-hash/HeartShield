import time
from typing import Dict
from threading import Lock

class TokenBlocklist:
    """
    In-memory session token blocklist for Layer 2 security.
    Tracks revoked JWTs until their expiration timestamp.
    """
    def __init__(self):
        self._revoked_tokens: Dict[str, float] = {}
        self._lock = Lock()

    def revoke_token(self, token: str, ttl_seconds: int = 86400) -> None:
        """Revokes a JWT token by adding it to the blocklist with an expiry timestamp."""
        if not token:
            return
        # Strip Bearer prefix if present
        if token.startswith("Bearer "):
            token = token[7:].strip()
            
        with self._lock:
            # Clean expired tokens periodically
            now = time.time()
            self._clean_expired_locked(now)
            self._revoked_tokens[token] = now + ttl_seconds

    def is_token_revoked(self, token: str) -> bool:
        """Checks if a given token has been revoked."""
        if not token:
            return False
        if token.startswith("Bearer "):
            token = token[7:].strip()

        with self._lock:
            now = time.time()
            expiry = self._revoked_tokens.get(token)
            if expiry is None:
                return False
            if now > expiry:
                # Expired from blocklist
                del self._revoked_tokens[token]
                return False
            return True

    def _clean_expired_locked(self, now: float) -> None:
        """Removes expired entries while holding the lock."""
        expired = [t for t, exp in self._revoked_tokens.items() if now > exp]
        for t in expired:
            del self._revoked_tokens[t]

token_blocklist = TokenBlocklist()
