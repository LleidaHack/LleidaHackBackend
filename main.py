from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from logging.config import dictConfig
import logging
from log_config import LogConfig

from src.User import router as User
from src.Hacker import router as Hacker
from src.HackerGroup import router as HackerGroup
from src.LleidaHacker import router as LleidaHacker
from src.LleidaHackerGroup import router as LleidaHackerGroup
# from src.CompanyUser.model import CompanyUser
from src.Company import router as Company
from src.CompanyUser import router as CompanyUser
from src.Event import router as Event
from src.Meal import router as Meal
from src.EventManagment import router as EventManagment
from src.Authentication import router as Authentication
from src.MailQueue import router as MailQueue
from src.Geocaching import router as Geocaching

from error import error_handler as eh
from error.AuthenticationException import AuthenticationException
from error.NotFoundException import NotFoundException
from error.ValidationException import ValidationException
from error.InvalidDataException import InvalidDataException
from error.InputException import InputException

dictConfig(LogConfig().dict())
logger = logging.getLogger("mycoolapp")

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
        "name": "EventManagment",
        "description": "Event Managment related endpoints"
    },
    {
        "name": "Authentication",
        "description": "Authentication related endpoints"
    },
]

app = FastAPI(title="LleidaHack API",
              description="LleidaHack API",
              version="2.0",
              docs_url='/docs',
              redoc_url='/redoc',
              openapi_url='/openapi.json',
              openapi_tags=tags_metadata,
              debug=True,
              swagger_ui_parameters={"syntaxHighlight.theme": "obsidian"})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.add_exception_handler(AuthenticationException,
                          eh.authentication_exception_handler)
app.add_exception_handler(NotFoundException, eh.not_found_exception_handler)
app.add_exception_handler(ValidationException, eh.validation_exception_handler)
app.add_exception_handler(InvalidDataException,
                          eh.invalid_data_exception_handler)
app.add_exception_handler(InputException, eh.input_exception_handler)

app.mount('/static', StaticFiles(directory='static'), name='static')

app.include_router(User.router)
app.include_router(Hacker.router)
app.include_router(HackerGroup.router)
app.include_router(LleidaHacker.router)
app.include_router(LleidaHackerGroup.router)
app.include_router(Company.router)
app.include_router(CompanyUser.router)
app.include_router(MailQueue.router)
app.include_router(Meal.router)
app.include_router(Event.router)
app.include_router(EventManagment.router)
app.include_router(Authentication.router)
app.include_router(Geocaching.router)


@app.get("/")
def root():
    return RedirectResponse(url='/docs')
