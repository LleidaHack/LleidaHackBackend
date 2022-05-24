from __future__ import annotations
from DatabaseService import DatabaseService
from Models import Event, Group, User
from DBConnector import database_connector
from PostgresConnector import PostgresConnector
from fastapi import Depends, FastAPI, Response, status
from fastapi.security import HTTPBearer
from utils import VerifyToken

# Scheme for the Authorization header
token_auth_scheme = HTTPBearer()

app = FastAPI()

service=DatabaseService()


@app.post("/login/{email}")
async def login(email: str, password: str):
    """
    Login a user and return the token.
    """
    # Verify that the user is in the database
    if connector.get_user(email, password) is None:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)
    else:
        # Create a token
        token = VerifyToken.create_token(email)
        # Return the token
        return {"token": token}

@app.post("/register")
async def register(user: User):
    """
    Register a user and return the token.
    """
    # Verify that the user is not in the database
    if connector.get_user(user.username, user.password) is not None:
        return Response(status_code=status.HTTP_409_CONFLICT)
    else:
        # Create a token
        token = VerifyToken.create_token(user.username)
        # Return the token
        return {"token": token}

@app.post("password_reset")
async def password_reset(email: str):
    """
    Reset the password of a user.
    """
    # Verify that the user is in the database
    if connector.get_user(email) is None:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)
    else:
        # Create a token
        token = VerifyToken.create_token(email)
        # send an email with an url to reset the password
        #TODO
        # Return the token
        return {"token": token}

@app.get("/users",response_model=User)
async def getUsers() -> User:
    return service.getUsers()

@app.get("/user/{userId}")
async def getUser(userId: int, response: Response, token: str = Depends(token_auth_scheme)) -> User:
    result = VerifyToken(token.credentials).verify()
    if result.get("status"):
       response.status_code = status.HTTP_400_BAD_REQUEST
       return result
    return service.getUser(userId)

@app.post("/user")
async def addUser(payload:User, response: Response, token: str = Depends(token_auth_scheme)) -> int:
    result = VerifyToken(token.credentials).verify()
    if result.get("status"):
       response.status_code = status.HTTP_400_BAD_REQUEST
       return result
    return connector.addUser(payload)

@app.post("/user/{userId}/remove")
async def removeUser(userId:int, response: Response, token: str = Depends(token_auth_scheme)) -> int:
    result = VerifyToken(token.credentials).verify()
    if result.get("status"):
       response.status_code = status.HTTP_400_BAD_REQUEST
       return result
    return connector.removeUser(userId)

@app.post("/user/{userId}/ban")
async def banUser(userId:int, response: Response, token: str = Depends(token_auth_scheme)) -> int:
    result = VerifyToken(token.credentials).verify()
    if result.get("status"):
       response.status_code = status.HTTP_400_BAD_REQUEST
       return result
    return connector.banUser(userId)





@app.get("/events")
async def getEvents() -> list:
    return connector.getEvents()

@app.get("/event/{eventId}")
async def getEvent(eventId:int) -> Event:
    return connector.getEvent(eventId)

@app.post("/event")
async def addEvent(payload:Event, response: Response, token: str = Depends(token_auth_scheme)) -> int:
    result = VerifyToken(token.credentials).verify()
    if result.get("status"):
       response.status_code = status.HTTP_400_BAD_REQUEST
       return result
    return connector.addEvent(payload)

@app.get("/event/{eventId}/users")
async def getEventUsers(eventId:int, response: Response, token: str = Depends(token_auth_scheme)) -> list:
    result = VerifyToken(token.credentials).verify()
    if result.get("status"):
       response.status_code = status.HTTP_400_BAD_REQUEST
       return result
    return connector.getEventUsers(eventId)

@app.post("/event/{eventId}/add/{userId}")
async def addUserEvent(eventId:int, userId:int, response: Response, token: str = Depends(token_auth_scheme)) -> int:
    result = VerifyToken(token.credentials).verify()
    if result.get("status"):
       response.status_code = status.HTTP_400_BAD_REQUEST
       return result
    return connector.addUserEvent(eventId, userId)

@app.post("/event/{eventId}/remove")
async def removeEvent(eventId:int, response: Response, token: str = Depends(token_auth_scheme)) -> int:
    result = VerifyToken(token.credentials).verify()
    if result.get("status"):
       response.status_code = status.HTTP_400_BAD_REQUEST
       return result
    return connector.removeEvent(eventId)

@app.post("/event/{eventId}/approve/{userId}")
async def approveEventUser(eventId:int, userId:int, response: Response, token: str = Depends(token_auth_scheme)) -> int:
    result = VerifyToken(token.credentials).verify()
    if result.get("status"):
       response.status_code = status.HTTP_400_BAD_REQUEST
       return result
    return connector.removeEvent(eventId)

@app.post("/event/{eventId}/reject/{userId}")
async def rejectEventUser(eventId:int, userId:int, response: Response, token: str = Depends(token_auth_scheme)) -> int:
    result = VerifyToken(token.credentials).verify()
    if result.get("status"):
       response.status_code = status.HTTP_400_BAD_REQUEST
       return result
    return connector.removeEvent(eventId)


@app.get("/groups")
async def getGroups(response: Response, token: str = Depends(token_auth_scheme)) -> list:
    result = VerifyToken(token.credentials).verify()
    if result.get("status"):
       response.status_code = status.HTTP_400_BAD_REQUEST
       return result
    return connector.getGroups()

@app.post("/group")
async def addGroup(payload:Group, response: Response, token: str = Depends(token_auth_scheme)) -> int:
    result = VerifyToken(token.credentials).verify()
    if result.get("status"):
       response.status_code = status.HTTP_400_BAD_REQUEST
       return result
    return connector.addGroup(payload)

@app.get("/group/{groupId}")
async def getGroup(groupId:int, response: Response, token: str = Depends(token_auth_scheme)) -> Group:
    result = VerifyToken(token.credentials).verify()
    if result.get("status"):
       response.status_code = status.HTTP_400_BAD_REQUEST
       return result
    return connector.getGroup(groupId)

@app.post("/group/{groupId}/remove")
async def removeGroup(groupId:int, response: Response, token: str = Depends(token_auth_scheme)) -> int:
    result = VerifyToken(token.credentials).verify()
    if result.get("status"):
       response.status_code = status.HTTP_400_BAD_REQUEST
       return result
    return connector.removeGroup(groupId)

