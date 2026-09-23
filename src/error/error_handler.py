# from main import app
from fastapi.responses import JSONResponse


# @app.exception_handler(AuthenticationException)
def authentication_exception_handler(request, exc):
    return JSONResponse(
        status_code=401,
        content={
            "message": exc.message,
            **({"code": exc.code} if getattr(exc, "code", None) else {}),
        },
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


def initialize_exception_handler(request, exc):
    return JSONResponse(
        status_code=503,
        content={"message": exc.message},
    )


def authorization_exception_handler(request, exc):
    return JSONResponse(status_code=403, content={"message": exc.message})
