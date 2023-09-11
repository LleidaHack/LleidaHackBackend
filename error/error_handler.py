# from main import app
from fastapi.responses import JSONResponse

from error.AuthenticationException import AuthenticationException
from error.NotFoundException import NotFoundException
from error.ValidationException import ValidationException
from error.InvalidDataException import InvalidDataException
from error.InputException import InputException


# @app.exception_handler(AuthenticationException)
async def authentication_exception_handler(request, exc):
    return JSONResponse(
        status_code=401,
        content={"message": exc.message},
    )


async def not_found_exception_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"message": exc.message},
    )


async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"message": exc.message},
    )


async def invalid_data_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"message": exc.message},
    )


async def input_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"message": exc.message},
    )
