import logging
import sys

from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles

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


class App:
    def __init__(self, app):
        self.app = app

    def setup_routers(self):
        self.app.include_router(User.router)
        self.app.include_router(Hacker.router)
        self.app.include_router(HackerGroup.router)
        self.app.include_router(LleidaHacker.router)
        self.app.include_router(LleidaHackerGroup.router)
        self.app.include_router(Company.router)
        self.app.include_router(CompanyUser.router)
        self.app.include_router(MailQueue.router)
        self.app.include_router(Meal.router)
        self.app.include_router(Event.router)
        self.app.include_router(Authentication.router)
        self.app.include_router(Geocaching.router)
        """
        Simplify operation IDs so that generated API clients have simpler function
        names.

        Should be called only after all routes have been added.
        """
        for route in self.app.routes:
            if isinstance(route, APIRoute):
                route.operation_id = route.name
    
    def setup_middleware(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["*"],
        )
    
    def setup_exceptions(self):
        self.app.add_exception_handler(AuthenticationException,eh.authentication_exception_handler)
        self.app.add_exception_handler(NotFoundException, eh.not_found_exception_handler)
        self.app.add_exception_handler(ValidationException, eh.validation_exception_handler)
        self.app.add_exception_handler(InvalidDataException,
                                eh.invalid_data_exception_handler)
        self.app.add_exception_handler(InputException, eh.input_exception_handler)
    
    def setup_static_folder(self):
        self.app.mount('/static', StaticFiles(directory='static'), name='static')

    def setup_logger(self, logger):
        logger.setLevel(logging.DEBUG)
        stream_handler = logging.StreamHandler(sys.stdout)
        log_formatter = logging.Formatter("%(asctime)s [%(processName)s: %(process)d] [%(threadName)s: %(thread)d] [%(levelname)s] %(name)s: %(message)s")
        stream_handler.setFormatter(log_formatter)
        logger.addHandler(stream_handler)
        
    def setup_all(self, logger):
        self.setup_static_folder()
        self.setup_exceptions()
        self.setup_routers()
        self.setup_middleware()
        self.setup_logger(logger)