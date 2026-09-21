import pytest

from app.core.rate_limit import RateLimitExceeded, SlidingWindowRateLimiter


def test_allows_up_to_the_limit_then_raises():
    limiter = SlidingWindowRateLimiter(limit=3, window_seconds=60)

    limiter.check("key-a")
    limiter.check("key-a")
    limiter.check("key-a")
    with pytest.raises(RateLimitExceeded):
        limiter.check("key-a")


def test_keys_are_independent():
    limiter = SlidingWindowRateLimiter(limit=1, window_seconds=60)

    limiter.check("key-a")
    limiter.check("key-b")  # different key, not affected by key-a's hit


def test_hits_outside_the_window_are_forgotten():
    limiter = SlidingWindowRateLimiter(limit=1, window_seconds=0.05)

    limiter.check("key-a")
    with pytest.raises(RateLimitExceeded):
        limiter.check("key-a")

    import time

    time.sleep(0.06)
    limiter.check("key-a")  # window has rolled past the first hit
