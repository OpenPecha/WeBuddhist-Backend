import json
import logging
import time
from typing import Any, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from pecha_api.config import get, get_int

logger = logging.getLogger("pecha.request")

_SKIP_PATHS = frozenset({"/health"})


def _is_enabled() -> bool:
    return get("REQUEST_OBSERVABILITY_ENABLED").lower() in {"1", "true", "yes"}


def _memory_warn_threshold_mb() -> float:
    return float(get_int("REQUEST_OBSERVABILITY_MEMORY_WARN_MB"))


def _read_rss_mb() -> Optional[float]:
    """Read current process RSS in MB (Linux /proc; used on Render)."""
    try:
        with open("/proc/self/status", encoding="ascii") as proc_status:
            for line in proc_status:
                if line.startswith("VmRSS:"):
                    kb = int(line.split()[1])
                    return round(kb / 1024, 2)
    except OSError:
        return None
    return None


def _route_path(request: Request) -> str:
    route = request.scope.get("route")
    if route is not None and hasattr(route, "path"):
        return route.path
    return request.url.path


def _should_skip(path: str) -> bool:
    skip_paths = get("REQUEST_OBSERVABILITY_SKIP_PATHS")
    if not skip_paths:
        return path in _SKIP_PATHS
    configured = {item.strip() for item in skip_paths.split(",") if item.strip()}
    return path in configured


def _build_log_payload(
    request: Request,
    *,
    status_code: int,
    duration_ms: float,
    rss_before: Optional[float],
    rss_after: Optional[float],
    error: Optional[str] = None,
) -> dict[str, Any]:
    rss_delta: Optional[float] = None
    if rss_before is not None and rss_after is not None:
        rss_delta = round(rss_after - rss_before, 2)

    route = request.scope.get("route")
    route_name = getattr(route, "name", None) if route else None
    tags = list(getattr(route, "tags", []) or []) if route else []

    payload: dict[str, Any] = {
        "event": "request_complete",
        "method": request.method,
        "path": _route_path(request),
        "route_name": route_name,
        "raw_path": request.url.path,
        "status": status_code,
        "duration_ms": round(duration_ms, 2),
        "rss_mb_before": rss_before,
        "rss_mb_after": rss_after,
        "rss_delta_mb": rss_delta,
        "tags": tags,
    }
    if error:
        payload["error"] = error
    return payload


class RequestObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if not _is_enabled() or _should_skip(request.url.path):
            return await call_next(request)

        rss_before = _read_rss_mb()
        started = time.perf_counter()
        status_code = 500
        error_msg: Optional[str] = None
        response: Optional[Response] = None

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {exc}"
            logger.error(
                "Unhandled exception for %s %s: %s",
                request.method,
                _route_path(request),
                error_msg,
                exc_info=exc,
            )
            raise
        finally:
            duration_ms = (time.perf_counter() - started) * 1000
            rss_after = _read_rss_mb()
            payload = _build_log_payload(
                request,
                status_code=status_code,
                duration_ms=duration_ms,
                rss_before=rss_before,
                rss_after=rss_after,
                error=error_msg,
            )

            rss_delta = payload.get("rss_delta_mb")
            threshold = _memory_warn_threshold_mb()
            if error_msg or (rss_delta is not None and rss_delta >= threshold):
                logger.warning(json.dumps(payload, default=str))
            else:
                logger.info(json.dumps(payload, default=str))
