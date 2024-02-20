# from main import app
from fastapi.responses import JSONResponse

from src.error.AuthenticationException import AuthenticationException
from src.error.NotFoundException import NotFoundException
from src.error.ValidationException import ValidationException
from src.error.InvalidDataException import InvalidDataException
from src.error.InputException import InputException


# @app.exception_handler(AuthenticationException)
def authentication_exception_handler(request, exc):

    return JSONResponse(
        status_code=401,
        content={"message": exc.message},
    )


def not_found_exception_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"message": exc.message},
    )


def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"message": exc.message},
    )


def invalid_data_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"message": exc.message},
    )


def input_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"message": exc.message},
    )
