import os
import sys
import pytest

# Ensure Back-end root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.rate_limiter import rate_limiter, ip_failed_login_tracker


@pytest.fixture(autouse=True)
def reset_rate_limiters_between_tests():
    """
    Ensures complete test isolation by resetting in-memory rate limiters
    and IP tracking state before and after every test execution.
    Prevents failure accumulation and state pollution across tests running under 'testclient' IP.
    """
    rate_limiter.reset()
    ip_failed_login_tracker.reset()
    yield
    rate_limiter.reset()
    ip_failed_login_tracker.reset()
