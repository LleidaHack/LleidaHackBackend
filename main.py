# from __future__ import annotations

from routers import user
from routers import hacker
from routers import lleidahacker
from routers import company


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

app.include_router(user.router)
app.include_router(hacker.router)
app.include_router(lleidahacker.router)
app.include_router(company.router)

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





# @app.get("/events")
# async def getEvents() -> list:
#     return service.getEvents()

# @app.get("/event/{eventId}")
# async def getEvent(eventId:int) -> Event:
#     return service.getEvent(eventId)

# @app.post("/event")
# async def addEvent(payload:Event, response: Response, token: str = Depends(token_auth_scheme)) -> int:
#     result = VerifyToken(token.credentials).verify()
#     if result.get("status"):
#        response.status_code = status.HTTP_400_BAD_REQUEST
#        return result
#     return service.addEvent(payload)

# @app.get("/event/{eventId}/users")
# async def getEventUsers(eventId:int, response: Response, token: str = Depends(token_auth_scheme)) -> list:
#     result = VerifyToken(token.credentials).verify()
#     if result.get("status"):
#        response.status_code = status.HTTP_400_BAD_REQUEST
#        return result
#     return service.getEventUsers(eventId)

# @app.post("/event/{eventId}/add/{userId}")
# async def addUserEvent(eventId:int, userId:int, response: Response, token: str = Depends(token_auth_scheme)) -> int:
#     result = VerifyToken(token.credentials).verify()
#     if result.get("status"):
#        response.status_code = status.HTTP_400_BAD_REQUEST
#        return result
#     return service.addUserEvent(eventId, userId)

# @app.post("/event/{eventId}/remove")
# async def removeEvent(eventId:int, response: Response, token: str = Depends(token_auth_scheme)) -> int:
#     result = VerifyToken(token.credentials).verify()
#     if result.get("status"):
#        response.status_code = status.HTTP_400_BAD_REQUEST
#        return result
#     return service.removeEvent(eventId)

# @app.post("/event/{eventId}/approve/{userId}")
# async def approveEventUser(eventId:int, userId:int, response: Response, token: str = Depends(token_auth_scheme)) -> int:
#     result = VerifyToken(token.credentials).verify()
#     if result.get("status"):
#        response.status_code = status.HTTP_400_BAD_REQUEST
#        return result
#     return service.removeEvent(eventId)

# @app.post("/event/{eventId}/reject/{userId}")
# async def rejectEventUser(eventId:int, userId:int, response: Response, token: str = Depends(token_auth_scheme)) -> int:
#     result = VerifyToken(token.credentials).verify()
#     if result.get("status"):
#        response.status_code = status.HTTP_400_BAD_REQUEST
#        return result
#     return service.removeEvent(eventId)


# @app.get("/groups")
# async def getGroups(response: Response, token: str = Depends(token_auth_scheme)) -> list:
#     result = VerifyToken(token.credentials).verify()
#     if result.get("status"):
#        response.status_code = status.HTTP_400_BAD_REQUEST
#        return result
#     return service.getGroups()

# @app.post("/group")
# async def addGroup(payload:Group, response: Response, token: str = Depends(token_auth_scheme)) -> int:
#     result = VerifyToken(token.credentials).verify()
#     if result.get("status"):
#        response.status_code = status.HTTP_400_BAD_REQUEST
#        return result
#     return service.addGroup(payload)

# @app.get("/group/{groupId}")
# async def getGroup(groupId:int, response: Response, token: str = Depends(token_auth_scheme)) -> Group:
#     result = VerifyToken(token.credentials).verify()
#     if result.get("status"):
#        response.status_code = status.HTTP_400_BAD_REQUEST
#        return result
#     return service.getGroup(groupId)

# @app.post("/group/{groupId}/remove")
# async def removeGroup(groupId:int, response: Response, token: str = Depends(token_auth_scheme)) -> int:
#     result = VerifyToken(token.credentials).verify()
#     if result.get("status"):
#        response.status_code = status.HTTP_400_BAD_REQUEST
#        return result
#     return service.removeGroup(groupId)
