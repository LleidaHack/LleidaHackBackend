from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from logging.config import dictConfig
import logging
from log_config import LogConfig

from routers import user
from routers import hacker
from routers import hackergroup
from routers import lleidahacker
from routers import lleidahackergroup
from routers import company
from routers import companyuser
from routers import event
from routers import meal
from routers import eventmanagment
from routers import authentication
from routers import utils

from error import error_handler as eh
from error.AuthenticationException import AuthenticationException
from error.NotFoundException import NotFoundException
from error.ValidationException import ValidationException
from error.InvalidDataException import InvalidDataException
from error.InputException import InputException

dictConfig(LogConfig().dict())
logger = logging.getLogger("mycoolapp")

tags_metadata = [
    # {
    #     "name": "User",
    #     "description": "User related endpoints"
    # },
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
    {
        "name": "Utils",
        "description": "Utils related endpoints"
    },
]

app = FastAPI(title="LleidaHack API",
              description="LleidaHack API",
              version="2.0",
              docs_url='/docs',
              redoc_url='/redoc',
              openapi_url='/openapi.json',
              openapi_tags=tags_metadata,
              debug=True)

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

# app.include_router(user.router)
app.include_router(hacker.router)
app.include_router(hackergroup.router)
app.include_router(lleidahacker.router)
app.include_router(lleidahackergroup.router)
app.include_router(company.router)
app.include_router(companyuser.router)
app.include_router(event.router)
app.include_router(meal.router)
app.include_router(eventmanagment.router)
app.include_router(authentication.router)
app.include_router(utils.router)


# @app.middleware("https")
# async def check_token_middleware(request: Request, call_next):
#     try:
#         if request.url.path != "/docs" and request.url.path != "/redoc":
#             authentication.check_token(request)
#     except Exception as e:
#         logger.error(e)
#         raise AuthenticationException()

#     response = await call_next(request)
#     return response

@app.get("/")
def root():
    return RedirectResponse(url='/docs')
