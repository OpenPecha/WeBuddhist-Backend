import secrets

from fastapi import Header, HTTPException
from starlette import status

from pecha_api.config import get


async def verify_dispatch_token(
    x_dispatch_token: str = Header(..., alias="X-Dispatch-Token"),
) -> None:
    expected = get("NOTIFICATION_DISPATCH_SECRET_TOKEN")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dispatch endpoint is not configured",
        )
    if not secrets.compare_digest(x_dispatch_token, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid dispatch token",
        )
