import logging

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from pecha_api.config import get, get_float

logger = logging.getLogger("pecha.sentry")


def init_sentry() -> None:
    dsn = get("SENTRY_DSN")
    if not dsn:
        return

    sentry_sdk.init(
        dsn=dsn,
        environment=get("SENTRY_ENVIRONMENT"),
        release=get("VERSION"),
        traces_sample_rate=get_float("SENTRY_TRACES_SAMPLE_RATE"),
        profiles_sample_rate=get_float("SENTRY_PROFILES_SAMPLE_RATE"),
        integrations=[StarletteIntegration(), FastApiIntegration()],
    )
    logger.info("Sentry initialized (environment=%s)", get("SENTRY_ENVIRONMENT"))
