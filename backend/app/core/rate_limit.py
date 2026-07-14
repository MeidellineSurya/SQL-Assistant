import threading
import time
from collections import defaultdict, deque

from fastapi import Depends, HTTPException, status

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.models.user import User


class RateLimitExceeded(Exception):
    def __init__(self, retry_after_seconds: float):
        self.retry_after_seconds = retry_after_seconds


class SlidingWindowLimiter:
    """In-memory per-key sliding window. Fine for a single instance (this
    app's current Render deployment); a horizontally-scaled deployment would
    need a shared store (e.g. Redis) since each process would otherwise track
    its own independent counters."""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > self.window_seconds:
                hits.popleft()
            if len(hits) >= self.max_requests:
                raise RateLimitExceeded(self.window_seconds - (now - hits[0]))
            hits.append(now)


# Shared across the AI-calling endpoints (generate, explain, chart suggest/
# generate) — one budget per user for "how many times can you make us call
# Groq per minute", not a separate budget per endpoint.
_ai_limiter = SlidingWindowLimiter(settings.rate_limit_max_requests, settings.rate_limit_window_seconds)


def check_ai_rate_limit(current_user: User = Depends(get_current_user)) -> None:
    try:
        _ai_limiter.check(str(current_user.id))
    except RateLimitExceeded as exc:
        retry_after = int(exc.retry_after_seconds) + 1
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"rate limit exceeded — retry after {retry_after}s",
            headers={"Retry-After": str(retry_after)},
        ) from exc
