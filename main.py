from __future__ import annotations
from Models import Event, Group, User
from connector import database_connector
from fastapi import Depends, FastAPI, Response, status
from fastapi.security import HTTPBearer
from utils import VerifyToken

# Scheme for the Authorization header
token_auth_scheme = HTTPBearer()

app = FastAPI()

connector=database_connector()

@app.get("/users",response_model=User)
def getUsers() -> User:
    return connector.getUsers()

@app.get("/user/{userId}")
def getUser(userId: int, response: Response, token: str = Depends(token_auth_scheme)) -> User:
    result = VerifyToken(token.credentials).verify()
    if result.get("status"):
       response.status_code = status.HTTP_400_BAD_REQUEST
       return result
    return connector.getUser(userId)

@app.post("/user")
def addUser(payload:User, response: Response, token: str = Depends(token_auth_scheme)) -> int:
    result = VerifyToken(token.credentials).verify()
    if result.get("status"):
       response.status_code = status.HTTP_400_BAD_REQUEST
       return result
    return connector.addUser(payload)

@app.post("/user/{userId}/remove")
def removeUser(userId:int, response: Response, token: str = Depends(token_auth_scheme)) -> int:
    result = VerifyToken(token.credentials).verify()
    if result.get("status"):
       response.status_code = status.HTTP_400_BAD_REQUEST
       return result
    return connector.removeUser(userId)

@app.post("/user/{userId}/ban")
def banUser(userId:int, response: Response, token: str = Depends(token_auth_scheme)) -> int:
    result = VerifyToken(token.credentials).verify()
    if result.get("status"):
       response.status_code = status.HTTP_400_BAD_REQUEST
       return result
    return connector.banUser(userId)





@app.get("/events")
def getEvents() -> list:
    return connector.getEvents()

@app.get("/event/{eventId}")
def getEvent(eventId:int) -> Event:
    return connector.getEvent(eventId)

@app.post("/event")
def addEvent(payload:Event, response: Response, token: str = Depends(token_auth_scheme)) -> int:
    result = VerifyToken(token.credentials).verify()
    if result.get("status"):
       response.status_code = status.HTTP_400_BAD_REQUEST
       return result
    return connector.addEvent(payload)

@app.get("/event/{eventId}/users")
def getEventUsers(eventId:int, response: Response, token: str = Depends(token_auth_scheme)) -> list:
    result = VerifyToken(token.credentials).verify()
    if result.get("status"):
       response.status_code = status.HTTP_400_BAD_REQUEST
       return result
    return connector.getEventUsers(eventId)

@app.post("/event/{eventId}/add/{userId}")
def addUserEvent(eventId:int, userId:int, response: Response, token: str = Depends(token_auth_scheme)) -> int:
    result = VerifyToken(token.credentials).verify()
    if result.get("status"):
       response.status_code = status.HTTP_400_BAD_REQUEST
       return result
    return connector.addUserEvent(eventId, userId)

@app.post("/event/{eventId}/remove")
def removeEvent(eventId:int, response: Response, token: str = Depends(token_auth_scheme)) -> int:
    result = VerifyToken(token.credentials).verify()
    if result.get("status"):
       response.status_code = status.HTTP_400_BAD_REQUEST
       return result
    return connector.removeEvent(eventId)

@app.post("/event/{eventId}/approve/{userId}")
def approveEventUser(eventId:int, userId:int, response: Response, token: str = Depends(token_auth_scheme)) -> int:
    result = VerifyToken(token.credentials).verify()
    if result.get("status"):
       response.status_code = status.HTTP_400_BAD_REQUEST
       return result
    return connector.removeEvent(eventId)

@app.post("/event/{eventId}/reject/{userId}")
def rejectEventUser(eventId:int, userId:int, response: Response, token: str = Depends(token_auth_scheme)) -> int:
    result = VerifyToken(token.credentials).verify()
    if result.get("status"):
       response.status_code = status.HTTP_400_BAD_REQUEST
       return result
    return connector.removeEvent(eventId)


@app.get("/groups")
def getGroups(response: Response, token: str = Depends(token_auth_scheme)) -> list:
    result = VerifyToken(token.credentials).verify()
    if result.get("status"):
       response.status_code = status.HTTP_400_BAD_REQUEST
       return result
    return connector.getGroups()

@app.post("/group")
def addGroup(payload:Group, response: Response, token: str = Depends(token_auth_scheme)) -> int:
    result = VerifyToken(token.credentials).verify()
    if result.get("status"):
       response.status_code = status.HTTP_400_BAD_REQUEST
       return result
    return connector.addGroup(payload)

@app.get("/group/{groupId}")
def getGroup(groupId:int, response: Response, token: str = Depends(token_auth_scheme)) -> Group:
    result = VerifyToken(token.credentials).verify()
    if result.get("status"):
       response.status_code = status.HTTP_400_BAD_REQUEST
       return result
    return connector.getGroup(groupId)

@app.post("/group/{groupId}/remove")
def removeGroup(groupId:int, response: Response, token: str = Depends(token_auth_scheme)) -> int:
    result = VerifyToken(token.credentials).verify()
    if result.get("status"):
       response.status_code = status.HTTP_400_BAD_REQUEST
       return result
    return connector.removeGroup(groupId)

