from __future__ import annotations

import structlog

from app.core.config import get_settings

logger = structlog.get_logger(__name__)


def init_sentry() -> None:
    """Start Sentry when SENTRY_DSN is set. Missing DSN leaves monitoring off."""
    settings = get_settings()
    if not settings.sentry_dsn:
        logger.info("sentry_disabled")
        return
    import sentry_sdk

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        send_default_pii=False,
        traces_sample_rate=0.0,
    )
    logger.info("sentry_enabled", environment=settings.environment)
