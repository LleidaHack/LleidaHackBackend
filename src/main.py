from routers import user
from routers import hacker
from routers import hackergroup
from routers import lleidahacker
from routers import lleidahackergroup
from routers import company
from routers import companyuser
from routers import event
from routers import eventmanagment
from routers import authentication
from routers import utils

from fastapi import Depends, FastAPI, Response, status, Request
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from logging.config import dictConfig
import logging
from LogConfig import LogConfig

dictConfig(LogConfig().dict())
logger = logging.getLogger("mycoolapp")



tags_metadata = [
    {"name": "User", "description": "User related endpoints"},
    {"name": "Hacker", "description": "Hacker related endpoints"},
    {"name": "Hacker Group", "description": "Hacker Group related endpoints"},
    {"name": "LleidaHacker", "description": "LleidaHacker related endpoints"},
    {"name": "LleidaHacker Group", "description": "LleidaHacker Group related endpoints"},
    {"name": "Company", "description": "Company related endpoints"},
    {"name": "Event", "description": "Event related endpoints"},
    {"name": "Authentication", "description": "Authentication related endpoints"},
    {"name": "Utils", "description": "Utils related endpoints"},
    {"name": "EventManagment", "description": "Event Managment related endpoints"},
]

app = FastAPI(title="LleidaHack API",
              description="LleidaHack API",
              version="2.0",
              docs_url='/docs',
              redoc_url='/redoc',
              openapi_url='/openapi.json',
              openapi_tags=tags_metadata,
              debug=True
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount('/static', StaticFiles(directory='static'), name='static')

app.include_router(user.router)
app.include_router(hacker.router)
app.include_router(hackergroup.router)
app.include_router(lleidahacker.router)
app.include_router(lleidahackergroup.router)
app.include_router(company.router)
app.include_router(companyuser.router)
app.include_router(event.router)
app.include_router(eventmanagment.router)
app.include_router(authentication.router)
app.include_router(utils.router)

@app.get("/")
def root():
    return RedirectResponse(url='/docs')