import time
import threading
import ipaddress
import os
from collections import defaultdict
from fastapi import Request, HTTPException, status
from typing import Dict, List, Tuple, Set


# Configurable Trusted Proxies (Local loopback and private subnets by default)
DEFAULT_TRUSTED_PROXIES = {
    "127.0.0.1",
    "::1",
    "localhost",
    "testclient"
}


def get_trusted_client_ip(request: Request) -> str:
    """
    Safely extracts client IP address behind reverse proxies.
    Only trusts X-Forwarded-For if the immediate connection originates from a trusted reverse proxy.
    Prevents header injection and spoofing.
    """
    peer_ip = request.client.host if request.client else "127.0.0.1"

    # Environment-configured trusted proxies
    env_proxies = os.getenv("TRUSTED_PROXIES", "")
    trusted_set = set(DEFAULT_TRUSTED_PROXIES)
    if env_proxies:
        trusted_set.update([p.strip() for p in env_proxies.split(",") if p.strip()])

    is_trusted = False
    if peer_ip in trusted_set:
        is_trusted = True
    else:
        try:
            peer_obj = ipaddress.ip_address(peer_ip)
            if peer_obj.is_loopback or peer_obj.is_private:
                is_trusted = True
        except ValueError:
            pass

    if is_trusted:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            parts = [p.strip() for p in forwarded.split(",") if p.strip()]
            if parts:
                # Return the original client IP (first entry)
                return parts[0]

    return peer_ip


class SlidingWindowRateLimiter:
    """
    Thread-safe sliding window in-memory rate limiter.
    Throttles aggressive authentication attempts, OTP generation spam, and brute force requests.
    """

    def __init__(self):
        self._history: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
        now = time.time()
        window_start = now - window_seconds

        with self._lock:
            timestamps = [t for t in self._history[key] if t > window_start]
            self._history[key] = timestamps

            if len(timestamps) >= max_requests:
                earliest = timestamps[0]
                retry_after = int(window_seconds - (now - earliest)) + 1
                return False, max(1, retry_after)

            self._history[key].append(now)
            return True, 0

    def reset(self, key: str = None):
        with self._lock:
            if key:
                self._history.pop(key, None)
            else:
                self._history.clear()


class IPFailedLoginTracker:
    """
    Tracks failed attempts by IP address and action scope to defend against
    horizontal credential stuffing and brute force attacks across accounts.
    Uses dedicated buckets for login, otp_verify, password_recovery, and account_unlock
    so that failed operations in one scope do not unintentionally exhaust another.
    """

    def __init__(self, max_failures: int = 10, window_seconds: int = 300, block_duration: int = 300):
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self.block_duration = block_duration
        self._failures: Dict[str, List[float]] = defaultdict(list)
        self._blocked_until: Dict[str, float] = {}
        self._lock = threading.Lock()

    def _get_key(self, ip: str, scope: str = "login") -> str:
        return f"{scope or 'login'}:{ip}"

    def is_ip_blocked(self, ip: str, scope: str = "login") -> Tuple[bool, int]:
        now = time.time()
        key = self._get_key(ip, scope)
        with self._lock:
            unblock_time = self._blocked_until.get(key)
            if unblock_time and now < unblock_time:
                remaining = int(unblock_time - now) + 1
                return True, max(1, remaining)

            # Clean expired block
            if unblock_time and now >= unblock_time:
                del self._blocked_until[key]
                self._failures.pop(key, None)

            return False, 0

    def record_failure(self, ip: str, scope: str = "login") -> Tuple[bool, int]:
        """
        Records a failed attempt for an IP within a given action scope.
        Returns (is_now_blocked, retry_after_seconds).
        """
        now = time.time()
        key = self._get_key(ip, scope)
        window_start = now - self.window_seconds

        with self._lock:
            timestamps = [t for t in self._failures[key] if t > window_start]
            timestamps.append(now)
            self._failures[key] = timestamps

            if len(timestamps) >= self.max_failures:
                unblock_time = now + self.block_duration
                self._blocked_until[key] = unblock_time
                return True, self.block_duration

            return False, 0

    def record_success(self, ip: str, scope: str = "login") -> None:
        """
        Cools down failed attempt count upon successful operation.
        """
        key = self._get_key(ip, scope)
        with self._lock:
            if key in self._failures:
                if self._failures[key]:
                    self._failures[key].pop()

    def reset(self, ip: str = None, scope: str = None) -> None:
        with self._lock:
            if ip and scope:
                key = self._get_key(ip, scope)
                self._failures.pop(key, None)
                self._blocked_until.pop(key, None)
            elif ip:
                target_suffix = f":{ip}"
                keys_to_remove = [k for k in self._failures if k.endswith(target_suffix) or k == ip]
                for k in keys_to_remove:
                    self._failures.pop(k, None)
                blocked_to_remove = [k for k in self._blocked_until if k.endswith(target_suffix) or k == ip]
                for k in blocked_to_remove:
                    self._blocked_until.pop(k, None)
            else:
                self._failures.clear()
                self._blocked_until.clear()


rate_limiter = SlidingWindowRateLimiter()
ip_failed_login_tracker = IPFailedLoginTracker(max_failures=10, window_seconds=300, block_duration=300)


def check_rate_limit(request: Request, max_requests: int = 15, window_seconds: int = 60, prefix: str = "rate"):
    """
    Dependency or helper to evaluate client rate limit based on client host IP.
    """
    client_ip = get_trusted_client_ip(request)
    path = request.url.path
    key = f"{prefix}:{path}:{client_ip}"

    allowed, retry_after = rate_limiter.is_allowed(key, max_requests, window_seconds)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {retry_after} seconds."
        )
