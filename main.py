# from __future__ import annotations

from routers import User
from routers import Hacker
from routers import HackerGroup
from routers import LleidaHacker
from routers import Company
from routers import Event


from sqlalchemy.orm import Session
from fastapi import Depends, FastAPI, Response, status, Request
from fastapi.security import HTTPBearer
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware


# Scheme for the Authorization header
token_auth_scheme = HTTPBearer()

tags_metadata = [
    {"name": "User", "description": "User related endpoints"},
    {"name": "Hacker", "description": "Hacker related endpoints"},
    {"name": "Hacker Group", "description": "Hacker Group related endpoints"},
    {"name": "LleidaHacker", "description": "LleidaHacker related endpoints"},
    {"name": "Company", "description": "Company related endpoints"},
    {"name": "Event", "description": "Event related endpoints"},
]

app = FastAPI(title="Lleida Hacke API",
              description="Lleida Hacker API",
              version="2.0",
              docs_url='/api/docs',
              redoc_url='/api/redoc',
              openapi_url='/api/openapi.json',
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

app.include_router(User.router)
app.include_router(Hacker.router)
app.include_router(HackerGroup.router)
app.include_router(LleidaHacker.router)
app.include_router(Company.router)
# app.include_router(Event.router)

# @app.post("/login/{email}")
# async def login(email: str, password: str):
#     """
#     Login a user and return the token.
#     """
#     # Verify that the user is in the database
#     if service.get_user(email, password) is None:
#         return Response(status_code=status.HTTP_401_UNAUTHORIZED)
#     else:
#         # Create a token
#         token = VerifyToken.create_token(email)
#         # Return the token
#         return {"token": token}

# @app.post("/register")
# async def register(user: User):
#     """
#     Register a user and return the token.
#     """
#     # Verify that the user is not in the database
#     if service.get_user(user.username, user.password) is not None:
#         return Response(status_code=status.HTTP_409_CONFLICT)
#     else:
#         # Create a token
#         token = VerifyToken.create_token(user.username)
#         # Return the token
#         return {"token": token}

# @app.post("password_reset")
# async def password_reset(email: str):
#     """
#     Reset the password of a user.
#     """
#     # Verify that the user is in the database
#     if service.get_user(email) is None:
#         return Response(status_code=status.HTTP_401_UNAUTHORIZED)
#     else:
#         # Create a token
#         token = VerifyToken.create_token(email)
#         # send an email with an url to reset the password
#         #TODO
#         # Return the token
#         return {"token": token}
