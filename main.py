from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi_sqlalchemy import DBSessionMiddleware

from App import App
from src.configuration.Configuration import Configuration

tags_metadata = [
    {
        "name": "User",
        "description": "User related endpoints"
    },
    {
        "name": "Hacker",
        "description": "Hacker related endpoints"
    },
    {
        "name": "Hacker Group",
        "description": "Hacker Group related endpoints"
    },
    {
        "name": "LleidaHacker",
        "description": "LleidaHacker related endpoints"
    },
    {
        "name": "LleidaHacker Group",
        "description": "LleidaHacker Group related endpoints"
    },
    {
        "name": "Company",
        "description": "Company related endpoints"
    },
    {
        "name": "Event",
        "description": "Event related endpoints"
    },
    {
        "name": "UserConfig",
        "description": "UserConfig related endpoints"
    },
    {
        "name": "Authentication",
        "description": "Authentication related endpoints"
    },
]

import logging

app = FastAPI(title="LleidaHack API",
              description="LleidaHack API",
              version="2.0",
              docs_url='/docs',
              redoc_url='/redoc',
              openapi_url='/openapi.json',
              openapi_tags=tags_metadata,
              debug=True,
              swagger_ui_parameters={"syntaxHighlight.theme": "obsidian"})

logger = logging.getLogger(__name__)


@app.get("/")
def root():
    return RedirectResponse(url='/docs')


# app.add_middleware(MaintenanceModeMiddleware, is_maintenance_mode=True)
# Configuration()
App(app).setup_all(logger)
