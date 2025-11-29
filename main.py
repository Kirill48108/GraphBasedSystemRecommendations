import logging

from fastapi import FastAPI

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.rate_limit import RateLimiterMiddleware


def create_app() -> FastAPI:
    setup_logging(logging.INFO)

    app = FastAPI(
        title="Movie Recommender API",
        version="0.1.0",
    )

    # Rate limiting middleware
    app.add_middleware(
        RateLimiterMiddleware,
        max_requests_per_minute=settings.rate_limit_requests_per_minute,
    )

    app.include_router(api_v1_router)

    return app


app = create_app()
