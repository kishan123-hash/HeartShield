import time
import threading
from collections import defaultdict
from fastapi import Request, HTTPException, status
from typing import Dict, List, Tuple


class SlidingWindowRateLimiter:
    """
    Layer 2 Security: Thread-safe sliding window in-memory rate limiter.
    Throttles aggressive authentication attempts, OTP generation spam, and brute force requests.
    """

    def __init__(self):
        # Map key -> list of timestamps
        self._history: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
        now = time.time()
        window_start = now - window_seconds

        with self._lock:
            # Clean timestamps older than window
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


rate_limiter = SlidingWindowRateLimiter()


def check_rate_limit(request: Request, max_requests: int = 15, window_seconds: int = 60, prefix: str = "rate"):
    """
    Dependency or helper to evaluate client rate limit based on client host IP.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip() or "127.0.0.1"
    else:
        client_ip = request.client.host if request.client else "127.0.0.1"
    path = request.url.path
    key = f"{prefix}:{path}:{client_ip}"

    allowed, retry_after = rate_limiter.is_allowed(key, max_requests, window_seconds)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {retry_after} seconds."
        )
