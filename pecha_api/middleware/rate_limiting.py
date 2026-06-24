import hashlib
import logging
from typing import Optional

from limits import parse_many
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from slowapi.wrappers import Limit
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from pecha_api.config import get, get_int

logger = logging.getLogger("pecha.ratelimit")

_DEFAULT_SKIP_PATHS = frozenset({"/health"})
_SCOPE = "global"


def _is_enabled() -> bool:
    return get("RATE_LIMIT_ENABLED").lower() in {"1", "true", "yes"}


def _storage_uri() -> str:
    configured = get("RATE_LIMIT_REDIS_URL").strip()
    if configured:
        return configured
    return get("CACHE_CONNECTION_STRING")


def _key_prefix() -> str:
    return get("RATE_LIMIT_KEY_PREFIX")


def _authenticated_limit() -> str:
    return f"{get_int('RATE_LIMIT_AUTHENTICATED_PER_HOUR')}/hour"


def _unauthenticated_limit() -> str:
    return f"{get_int('RATE_LIMIT_UNAUTHENTICATED_PER_HOUR')}/hour"


def _skip_paths() -> frozenset[str]:
    configured = get("RATE_LIMIT_SKIP_PATHS")
    if not configured:
        return _DEFAULT_SKIP_PATHS
    return frozenset(
        item.strip() for item in configured.split(",") if item.strip()
    )


def _should_skip(path: str) -> bool:
    return path in _skip_paths()


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return get_remote_address(request)


def rate_limit_key(request: Request) -> str:
    authorization = request.headers.get("Authorization", "")
    if authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
        if token:
            digest = hashlib.sha256(token.encode()).hexdigest()[:32]
            return f"auth:{digest}"
    return f"ip:{get_client_ip(request)}"


def limit_for_key(key: str) -> str:
    if key.startswith("auth:"):
        return _authenticated_limit()
    return _unauthenticated_limit()


def _build_limiter() -> Limiter:
    return Limiter(
        key_func=rate_limit_key,
        storage_uri=_storage_uri(),
        headers_enabled=True,
        enabled=_is_enabled(),
        key_prefix=_key_prefix(),
        in_memory_fallback_enabled=True,
        in_memory_fallback=[_unauthenticated_limit()],
    )


limiter = _build_limiter()


def _build_limit_object(limit_raw: str) -> Limit:
    limit_item = parse_many(limit_raw)[0]
    return Limit(
        limit=limit_item,
        key_func=rate_limit_key,
        scope=_SCOPE,
        per_method=False,
        methods=None,
        error_message="Too many requests. Please try again later.",
        exempt_when=None,
        cost=1,
        override_defaults=False,
    )


def _hit_args(limit_key: str) -> list[str]:
    args = [limit_key, _SCOPE]
    if limiter._key_prefix:
        args = [limiter._key_prefix] + args
    return [item for item in args if item]


def _check_rate_limit(request: Request) -> Optional[Limit]:
    limit_key = rate_limit_key(request)
    limit_raw = limit_for_key(limit_key)
    limit_item = parse_many(limit_raw)[0]
    hit_args = _hit_args(limit_key)
    request.state.view_rate_limit = (limit_item, hit_args)
    if limiter.limiter.hit(limit_item, *hit_args):
        return None
    return _build_limit_object(limit_raw)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if not limiter.enabled or _should_skip(request.url.path):
            return await call_next(request)

        failed_limit = _check_rate_limit(request)
        if failed_limit is not None:
            logger.warning(
                "Rate limit exceeded for key=%s path=%s",
                rate_limit_key(request),
                request.url.path,
            )
            return _rate_limit_exceeded_handler(
                request, RateLimitExceeded(failed_limit)
            )

        response = await call_next(request)
        if limiter._headers_enabled and hasattr(request.state, "view_rate_limit"):
            response = limiter._inject_headers(response, request.state.view_rate_limit)
        return response


def register_rate_limiting(app: Starlette) -> None:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    if limiter.enabled:
        app.add_middleware(RateLimitMiddleware)
