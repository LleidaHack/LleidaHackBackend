import logging
import time
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from App import App
from src import (
    # Register SQLAlchemy models through import side effects.
    imports,  # noqa: F401
)

tags_metadata = [
    {"name": "User", "description": "User related endpoints"},
    {"name": "UserConfig", "description": "UserConfig related endpoints"},
    {"name": "Hacker", "description": "Hacker related endpoints"},
    {"name": "Hacker Group", "description": "Hacker Group related endpoints"},
    {"name": "LleidaHacker", "description": "LleidaHacker related endpoints"},
    {
        "name": "LleidaHacker Group",
        "description": "LleidaHacker Group related endpoints",
    },
    {"name": "Company", "description": "Company related endpoints"},
    {"name": "CompanyUser", "description": "Company user related endpoints"},
    {"name": "Event", "description": "Event related endpoints"},
    {"name": "Meal", "description": "Meal related endpoints"},
    {"name": "Voucher", "description": "Physical check-in vouchers (badges) per event"},
    {"name": "Authentication", "description": "Authentication related endpoints"},
]


app = FastAPI(
    title="LleidaHack API",
    description="LleidaHack API",
    version="2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=tags_metadata,
    debug=False,
    swagger_ui_parameters={"syntaxHighlight.theme": "obsidian"},
)

logger = logging.getLogger(__name__)


@app.get("/")
def root():
    return RedirectResponse(url="/docs")


App(app).setup_all(logger)
from src.utils.health import router as health_router

app.include_router(health_router)


@app.middleware("http")
async def prevent_operations_caching(request, call_next):
    started = time.monotonic()
    try:
        request_id = str(UUID(request.headers.get("x-request-id", "")))
    except ValueError:
        request_id = str(uuid4())
    try:
        response = await call_next(request)
    except Exception:
        route = getattr(request.scope.get("route"), "path", "unmatched")
        logger.error(
            "Request failed request_id=%s method=%s route=%s",
            request_id,
            request.method,
            route,
        )
        raise
    response.headers["X-Request-ID"] = request_id
    elapsed_ms = round((time.monotonic() - started) * 1000)
    if response.status_code >= 500 or elapsed_ms >= 1000:
        route = getattr(request.scope.get("route"), "path", "unmatched")
        logger.warning(
            "Request diagnostic request_id=%s method=%s route=%s status=%s duration_ms=%s",
            request_id,
            request.method,
            route,
            response.status_code,
            elapsed_ms,
        )
    if request.url.path.startswith(
        ("/v1/operations/", "/v1/company-portal/", "/health/")
    ):
        response.headers["Cache-Control"] = "no-store, private, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response
