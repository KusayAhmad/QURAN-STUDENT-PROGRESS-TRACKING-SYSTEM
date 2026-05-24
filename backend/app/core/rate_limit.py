"""Rate limiting middleware using slowapi.

Default limits (configurable via settings):
  - 60 requests/minute per IP for most endpoints
  - 10 requests/minute for auth endpoints (login, refresh)
  - 200 requests/minute for read-heavy endpoints (surahs, analytics)

The limiter uses the client IP from the request. Behind a reverse proxy
(Nginx, Cloudflare), make sure X-Forwarded-For is passed.
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.core.config import get_settings


def _key_func(request: Request) -> str:
    """Key by IP. For authenticated endpoints you could also key by user_id."""
    return get_remote_address(request) or "unknown"


settings = get_settings()

limiter = Limiter(
    key_func=_key_func,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"],
    storage_uri="memory://",  # In-memory; swap to Redis URI for multi-process
)


def setup_rate_limiting(app):
    """Call from main.py after app creation."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def disable_rate_limiting():
    """Disable rate limiting for tests."""
    limiter.enabled = False
