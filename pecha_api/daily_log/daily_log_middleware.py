import asyncio
import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from pecha_api.daily_log.daily_log_service import record_daily_log_for_token


def _log_daily_log_task_error(task: asyncio.Task) -> None:
    if task.cancelled():
        return

    exception = task.exception()
    if exception is not None:
        logging.error("Daily log background task failed", exc_info=exception)


def schedule_daily_log(token: str) -> None:
    task = asyncio.create_task(record_daily_log_for_token(token=token))
    task.add_done_callback(_log_daily_log_task_error)


class DailyLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        authorization = request.headers.get("Authorization", "")
        if authorization.startswith("Bearer "):
            token = authorization.removeprefix("Bearer ").strip()
            if token:
                schedule_daily_log(token=token)

        return await call_next(request)
