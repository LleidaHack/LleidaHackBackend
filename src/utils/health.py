"""Bounded readiness checks without credentials or dependency error details."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from fastapi_sqlalchemy import db
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from src.configuration.Settings import settings

router = APIRouter(tags=["Health"])


@router.get("/health/live")
def live():
    return {"status": "ok"}


@router.get("/health/ready")
def ready():
    checks = {"database": False, "redis": not settings.rate_limit.enabled}
    try:
        db.session.execute(text("SET LOCAL statement_timeout = '1500ms'"))
        db.session.execute(text("SELECT 1"))
        checks["database"] = True
    except SQLAlchemyError:
        checks["database"] = False
    finally:
        db.session.rollback()
    if settings.rate_limit.enabled:
        try:
            with Redis.from_url(
                settings.rate_limit.redis_url,
                socket_connect_timeout=1,
                socket_timeout=1,
            ) as redis:
                checks["redis"] = bool(redis.ping())
        except RedisError:
            checks["redis"] = False
    healthy = all(checks.values())
    return JSONResponse(
        {"status": "ok" if healthy else "unavailable", "checks": checks},
        status_code=200 if healthy else 503,
        headers={"Cache-Control": "no-store"},
    )
