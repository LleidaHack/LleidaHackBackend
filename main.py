from __future__ import annotations
import datetime
import os
# from DatabaseService import DatabaseService
from utils import VerifyToken
from typing import List
from Models import User as ModelUser
from schema import User as SchemaUser
from dotenv import load_dotenv
from database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends, FastAPI, Response, status, Request
from fastapi.security import HTTPBearer
from fastapi.responses import JSONResponse



# load_dotenv('.env')

# Scheme for the Authorization header
token_auth_scheme = HTTPBearer()

app = FastAPI(title="API_NAME",
              description="API_DESC",
              version="0.2.0",
              docs_url='/api/docs',
              redoc_url='/api/redoc',
              openapi_url='/api/openapi.json')

# service=DatabaseService()

# app.add_middleware(DBSessionMiddleware, db_url=os.environ['DATABASE_URL'])

@app.exception_handler(ValueError)
async def value_error_exception_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"message": str(exc)},
    )


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

@app.get("/users")
async def getUsers(db: Session = Depends(get_db)):
    book = db.session.query(ModelUser).all()
    return book
    # return service.getUsers()

# @app.get("/user/{userId}")
# async def getUser(userId: int, response: Response, token: str = Depends(token_auth_scheme)) -> User:
#     result = VerifyToken(token.credentials).verify()
#     if result.get("status"):
#        response.status_code = status.HTTP_400_BAD_REQUEST
#        return result
#     return service.getUser(userId)

@app.post("/user")
# async def addUser(payload:User, response: Response, token: str = Depends(token_auth_scheme)) -> int:
async def addUser(payload:SchemaUser, response: Response, db: Session = Depends(get_db)) -> int:
    # result = VerifyToken(token.credentials).verify()
    # if result.get("status"):
    #    response.status_code = status.HTTP_400_BAD_REQUEST
    #    return result
    new_user = ModelUser(name=payload.name, 
                         email=payload.email,
                         password=payload.password,
                         nickname=payload.nickname,
                         birthdate = payload.birthdate,
                         food_restrictions=payload.food_restrictions,
                         telephone=payload.telephone,
                         address=payload.address,
                         shirtSize=payload.shirtSize)
    db.add(new_user)
    db.commit()
    # db.refresh(new_job)
    return {"success": True, "created_id": new_user.id}
    # return service.addUser(payload)

# @app.post("/user/{userId}/remove")
# async def removeUser(userId:int, response: Response, token: str = Depends(token_auth_scheme)) -> int:
#     result = VerifyToken(token.credentials).verify()
#     if result.get("status"):
#        response.status_code = status.HTTP_400_BAD_REQUEST
#        return result
#     return service.removeUser(userId)

# @app.post("/user/{userId}/ban")
# async def banUser(userId:int, response: Response, token: str = Depends(token_auth_scheme)) -> int:
#     result = VerifyToken(token.credentials).verify()
#     if result.get("status"):
#        response.status_code = status.HTTP_400_BAD_REQUEST
#        return result
#     return service.banUser(userId)





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


# service.addUser(User("t","t","",datetime.datetime.now(),"","","","",""))
