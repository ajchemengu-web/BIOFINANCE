"""
A minimal in-process sliding-window rate limiter — no Redis or other shared
store in this stack yet, so this only protects a single running instance.
`render.yaml` deploys exactly one web service instance today, so that's a
real (if narrow) guarantee for now; it stops being one the moment this app
scales to more than one instance, at which point this needs to move to a
shared store. Documented as a known limit, not silently assumed away.

First use: BioFinance ID push pairing's abuse surface (docs/security-model.md,
"Abuse surface: unsolicited push spam") — anyone who knows or brute-forces a
valid BioFinance ID can trigger a push to that person by opening a payment
request against it. This doesn't stop that outright, it just caps how often
it can happen from one merchant or against one BioFinance ID.
"""

import time
from collections import defaultdict


class RateLimitExceeded(Exception):
    pass


class SlidingWindowRateLimiter:
    def __init__(self, limit: int, window_seconds: float) -> None:
        self._limit = limit
        self._window_seconds = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str) -> None:
        """Records a hit for `key` and raises RateLimitExceeded if that
        pushes it over the limit within the window."""
        now = time.monotonic()
        cutoff = now - self._window_seconds
        hits = self._hits[key]
        while hits and hits[0] < cutoff:
            hits.pop(0)

        if len(hits) >= self._limit:
            raise RateLimitExceeded(
                f"Too many requests ({self._limit} per {int(self._window_seconds)}s) — try again shortly"
            )
        hits.append(now)
