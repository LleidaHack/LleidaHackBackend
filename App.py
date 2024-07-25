import logging
import sys

from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles
from fastapi_sqlalchemy import DBSessionMiddleware

from src.configuration.Configuration import Configuration
from src.versions.v1 import router as v1_router


class App:

    def __init__(self, app):
        self.app = app

    def setup_routers(self):
        self.app.include_router(v1_router)
        """
        Simplify operation IDs so that generated API clients have simpler function
        names.
        Should be called only after all routes have been added.
        """

        for route in self.app.routes:
            if isinstance(route, APIRoute):
                route.operation_id = route.tags[-1].replace(
                    ' ', '').lower() if len(route.tags) > 0 else ''
                route.operation_id += '_' + route.name
                # print(route.operation_id)

    def setup_middleware(self):
        self.app.add_middleware(DBSessionMiddleware,
                                db_url=Configuration.database.url)
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["*"],
        )

    def setup_exceptions(self):
        from src.error import error_handler as eh
        from src.error.AuthenticationException import AuthenticationException
        from src.error.InputException import InputException
        from src.error.InvalidDataException import InvalidDataException
        from src.error.NotFoundException import NotFoundException
        from src.error.ValidationException import ValidationException
        self.app.add_exception_handler(AuthenticationException,
                                       eh.authentication_exception_handler)
        self.app.add_exception_handler(NotFoundException,
                                       eh.not_found_exception_handler)
        self.app.add_exception_handler(ValidationException,
                                       eh.validation_exception_handler)
        self.app.add_exception_handler(InvalidDataException,
                                       eh.invalid_data_exception_handler)
        self.app.add_exception_handler(InputException,
                                       eh.input_exception_handler)

    def setup_static_folder(self):
        self.app.mount('/static',
                       StaticFiles(directory='static'),
                       name='static')

    def setup_logger(self, logger):
        logger.setLevel(logging.DEBUG)
        stream_handler = logging.StreamHandler(sys.stdout)
        log_formatter = logging.Formatter(
            "%(asctime)s [%(processName)s: %(process)d] [%(threadName)s: %(thread)d] [%(levelname)s] %(name)s: %(message)s"
        )
        stream_handler.setFormatter(log_formatter)
        logger.addHandler(stream_handler)

    def setup_all(self, logger):
        self.setup_static_folder()
        self.setup_middleware()
        self.setup_logger(logger)
        self.setup_exceptions()
        self.setup_routers()
