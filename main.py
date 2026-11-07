import logging

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


# app.add_middleware(MaintenanceModeMiddleware, is_maintenance_mode=True)
# Configuration()
App(app).setup_all(logger)


@app.middleware("http")
async def prevent_operations_caching(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/v1/operations/"):
        response.headers["Cache-Control"] = "no-store, private, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response
