import logging
from logging.config import dictConfig

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from log_config import LogConfig
from src.error import error_handler as eh
from src.error.AuthenticationException import AuthenticationException
from src.error.InputException import InputException
from src.error.InvalidDataException import InvalidDataException
from src.error.NotFoundException import NotFoundException
from src.error.ValidationException import ValidationException
from src.impl.Authentication import router as Authentication
from src.impl.Company import router as Company
from src.impl.CompanyUser import router as CompanyUser
from src.impl.Event import router as Event
from src.impl.Geocaching import router as Geocaching
from src.impl.Hacker import router as Hacker
from src.impl.HackerGroup import router as HackerGroup
from src.impl.LleidaHacker import router as LleidaHacker
from src.impl.LleidaHackerGroup import router as LleidaHackerGroup
from src.impl.MailQueue import router as MailQueue
from src.impl.Meal import router as Meal
from src.impl.User import router as User

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
app.include_router(Authentication.router)
app.include_router(Geocaching.router)


@app.get("/")
def root():
    return RedirectResponse(url='/docs')
