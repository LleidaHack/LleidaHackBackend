# from __future__ import annotations
# import datetime
# import os
# from DatabaseService import DatabaseService
# from utils import VerifyToken
from Models import User as ModelUser
from Models import Hacker as ModelHacker
from Models import HackerGroup as ModelHackerGroup
from Models import Company as ModelCompany
from Models import LleidaHacker as ModelLleidaHacker
from Models import LleidaHackerGroup as ModelLleidaHackerGroup

from schema import User as SchemaUser
from schema import Hacker as SchemaHacker
from schema import HackerGroup as SchemaHackerGroup
from schema import Company as SchemaCompany
from schema import LleidaHacker as SchemaLleidaHacker
from schema import LleidaHackerGroup as SchemaLleidaHackerGroup

from database import get_db
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
              debug=True,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routers import user
app.include_router(user.router)

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

# @app.get("/users", tags=["User"])
# async def get_users(db: Session = Depends(get_db)):
#     return db.query(ModelUser).all()
#     # return service.getUsers()

# @app.get("/user/{userId}", tags=["User"])
# # async def getUser(userId: int, response: Response, token: str = Depends(token_auth_scheme)):
# async def get_user(userId: int, response: Response, db: Session = Depends(get_db)):
#     # result = VerifyToken(token.credentials).verify()
#     # if result.get("status"):
#     #    response.status_code = status.HTTP_400_BAD_REQUEST
#     #    return result
#     return db.query(ModelUser).filter(ModelUser.id == userId).first()

# @app.post("/user", tags=["User"])
# # async def addUser(payload:User, response: Response, token: str = Depends(token_auth_scheme)) -> int:
# async def add_user(payload:SchemaUser, response: Response, db: Session = Depends(get_db)):
#     # result = VerifyToken(token.credentials).verify()
#     # if result.get("status"):
#     #    response.status_code = status.HTTP_400_BAD_REQUEST
#     #    return result
#     new_user = ModelUser(name=payload.name, 
#                          email=payload.email,
#                          password=payload.password,
#                          nickname=payload.nickname,
#                          birthdate = payload.birthdate,
#                          food_restrictions=payload.food_restrictions,
#                          telephone=payload.telephone,
#                          address=payload.address,
#                          shirt_size=payload.shirt_size)
#     db.add(new_user)
#     db.commit()
#     # db.refresh(new_job)
#     return {"success": True, "created_id": new_user.id}
#     # return service.addUser(payload)

# @app.put("/user/{userId}", tags=["User"])
# # async def updateUser(userId: int, payload: User, response: Response, token: str = Depends(token_auth_scheme)):
# async def update_user(userId: int, payload: SchemaUser, response: Response, db: Session = Depends(get_db)):
#     # result = VerifyToken(token.credentials).verify()
#     # if result.get("status"):
#     #    response.status_code = status.HTTP_400_BAD_REQUEST
#     #    return result
#     user = db.query(ModelUser).filter(ModelUser.id == userId).first()
#     user.name = payload.name
#     user.email = payload.email
#     user.password = payload.password
#     user.nickname = payload.nickname
#     user.birthdate = payload.birthdate
#     user.food_restrictions = payload.food_restrictions
#     user.telephone = payload.telephone
#     user.address = payload.address
#     user.shirt_size = payload.shirt_size
#     db.commit()

# @app.delete("/user/{userId}", tags=["User"])
# # async def removeUser(userId:int, response: Response, token: str = Depends(token_auth_scheme)) -> int:
# async def remove_user(userId:int, response: Response, db: Session = Depends(get_db)):
# #     result = VerifyToken(token.credentials).verify()
# #     if result.get("status"):
# #        response.status_code = status.HTTP_400_BAD_REQUEST
# #        return result
#     return db.query(ModelUser).filter(ModelUser.id == userId).delete()

@app.get("/hackers", tags=["Hacker"])
async def get_hackers(db: Session = Depends(get_db)):
    return db.query(ModelHacker).all()

@app.get("/hacker/{hackerId}", tags=["Hacker"])
async def get_hacker(hackerId: int, response: Response, db: Session = Depends(get_db)):
    return db.query(ModelHacker).filter(ModelHacker.id == hackerId).first()

@app.post("/hacker", tags=["Hacker"])
async def add_hacker(payload:SchemaHacker, response: Response, db: Session = Depends(get_db)):
    new_hacker = ModelHacker(name=payload.name, 
                         email=payload.email,
                         password=payload.password,
                         nickname=payload.nickname,
                         birthdate = payload.birthdate,
                         food_restrictions=payload.food_restrictions,
                         telephone=payload.telephone,
                         address=payload.address,
                         shirt_size=payload.shirt_size)
    db.add(new_hacker)
    db.commit()
    return {"success": True, "created_id": new_hacker.id}

@app.put("/hacker/{hackerId}", tags=["Hacker"])
async def update_hacker(hackerId: int, payload: SchemaHacker, response: Response, db: Session = Depends(get_db)):
    hacker = db.query(ModelHacker).filter(ModelHacker.id == hackerId).first()
    hacker.name = payload.name
    hacker.email = payload.email
    hacker.password = payload.password
    hacker.nickname = payload.nickname
    hacker.birthdate = payload.birthdate
    hacker.food_restrictions = payload.food_restrictions
    hacker.telephone = payload.telephone
    hacker.address = payload.address
    hacker.shirt_size = payload.shirt_size
    db.commit()

@app.post("/hacker/{userId}/ban", tags=["Hacker"])
# async def banUser(userId:int, response: Response, token: str = Depends(token_auth_scheme)) -> int:
async def ban_hacker(userId:int, db: Session = Depends(get_db)) -> int:
    # result = VerifyToken(token.credentials).verify()
    # if result.get("status"):
    #    response.status_code = status.HTTP_400_BAD_REQUEST
    #    return result
    if db.query(ModelUser).filter(ModelUser.id == userId).first().type=="hacker":
        return db.query(ModelUser).filter(ModelUser.id == userId).update({"banned":1})
    else:
        return {"success": False}


@app.post("/hacker/{userId}/unban", tags=["Hacker"])
# async def unbanUser(userId:int, response: Response, token: str = Depends(token_auth_scheme)) -> int:
async def unban_hacker(userId:int, response: Response, db: Session = Depends(get_db)) -> int:
    # result = VerifyToken(token.credentials).verify()
    # if result.get("status"):
    #    response.status_code = status.HTTP_400_BAD_REQUEST
    #    return result
    if db.query(ModelUser).filter(ModelUser.id == userId).first().type=="hacker":
        return db.query(ModelUser).filter(ModelUser.id == userId).update({"banned":0})
    else:
        return {"success": False}

@app.delete("/hacker/{userId}", tags=["Hacker"])
# async def deleteUser(userId:int, response: Response, token: str = Depends(token_auth_scheme)) -> int:
async def delete_hacker(userId:int, response: Response, db: Session = Depends(get_db)):
    # result = VerifyToken(token.credentials).verify()
    # if result.get("status"):
    #    response.status_code = status.HTTP_400_BAD_REQUEST
    #    return result
    db.query(ModelHacker).filter(ModelHacker.id == userId).delete()
    db.query(ModelUser).filter(ModelUser.id == userId).delete()
    return {"success": True}

@app.get("/hacker/groups", tags=["Hacker"])
async def get_hacker_groups(db: Session = Depends(get_db)):
    return db.query(ModelHackerGroup).all()

@app.get("/hacker/group/{groupId}", tags=["Hacker"])
async def get_hacker_group(groupId: int, response: Response, db: Session = Depends(get_db)):
    return db.query(ModelHackerGroup).filter(ModelHackerGroup.id == groupId).first()

@app.post("/hacker/group", tags=["Hacker"])
async def add_hacker_group(payload:SchemaHackerGroup, response: Response, db: Session = Depends(get_db)):
    new_hacker_group = ModelHackerGroup(name=payload.name,
                                        description=payload.description,
    )
    db.add(new_hacker_group)
    db.commit()
    return {"success": True, "created_id": new_hacker_group.id}

@app.put("/hacker/group/{groupId}", tags=["Hacker"])
async def update_hacker_group(groupId: int, payload: SchemaHackerGroup, response: Response, db: Session = Depends(get_db)):
    hacker_group = db.query(ModelHackerGroup).filter(ModelHackerGroup.id == groupId).first()
    hacker_group.name = payload.name
    hacker_group.description = payload.description
    db.commit()


@app.delete("/hacker/group/{groupId}", tags=["Hacker"])
async def delete_hacker_group(groupId:int, response: Response, db: Session = Depends(get_db)):
    # result = VerifyToken(token.credentials).verify()
    # if result.get("status"):
    #    response.status_code = status.HTTP_400_BAD_REQUEST
    #    return result
    db.query(ModelHackerGroup).filter(ModelHackerGroup.id == groupId).delete()
    return {"success": True}

@app.get("/hacker/group/{groupId}/members", tags=["Hacker"])
async def get_hacker_group_members(groupId: int, response: Response, db: Session = Depends(get_db)):
    return db.query(ModelHackerGroup).filter(ModelHackerGroup.id == groupId).all().members

@app.post("/hacker/group/{groupId}/add/{hackerId}", tags=["Hacker","HackerGroup"])
async def add_hacker_to_group(groupId: int, hackerId: int, response: Response, db: Session = Depends(get_db)):
    hacker_group = db.query(ModelHackerGroup).filter(ModelHackerGroup.id == groupId).first()
    hacker = db.query(ModelHacker).filter(ModelHacker.id == hackerId).first()
    hacker_group.members.append(hacker)
    db.commit()


@app.get("/companies", tags=["Company"])
async def get_companies(db: Session = Depends(get_db)):
    return db.query(ModelCompany).all()

@app.get("/company/{companyId}", tags=["Company"])
async def get_company(companyId: int, response: Response, db: Session = Depends(get_db)):
    return db.query(ModelCompany).filter(ModelCompany.id == companyId).first()

@app.post("/company", tags=["Company"])
async def add_company(payload:SchemaCompany, response: Response, db: Session = Depends(get_db)):
    new_company = ModelCompany(name=payload.name, 
                         email=payload.email,
                         password=payload.password,
                         nickname=payload.nickname,
                         birthdate = payload.birthdate,
                         food_restrictions=payload.food_restrictions,
                         telephone=payload.telephone,
                         address=payload.address,
                         shirt_size=payload.shirt_size)
    db.add(new_company)
    db.commit()
    return {"success": True, "created_id": new_company.id}

@app.delete("/company/{userId}", tags=["Company"])
# async def deleteUser(userId:int, response: Response, token: str = Depends(token_auth_scheme)) -> int:
async def delete_company(userId:int, response: Response, db: Session = Depends(get_db)):
    # result = VerifyToken(token.credentials).verify()
    # if result.get("status"):
    #    response.status_code = status.HTTP_400_BAD_REQUEST
    #    return result
    db.query(ModelCompany).filter(ModelCompany.id == userId).delete()
    db.query(ModelUser).filter(ModelUser.id == userId).delete()
    return {"success": True}

@app.get("/lleidahacker", tags=["LleidaHacker"])
async def get_lleidahacker(db: Session = Depends(get_db)):
    return db.query(ModelLleidaHacker).all()

@app.get("/lleidahacker/{userId}", tags=["LleidaHacker"])
async def get_lleidahacker(userId: int, response: Response, db: Session = Depends(get_db)):
    return db.query(ModelLleidaHacker).filter(ModelLleidaHacker.id == userId).first()

@app.post("/lleidahacker", tags=["LleidaHacker"])
async def add_lleidahacker(payload:SchemaLleidaHacker, response: Response, db: Session = Depends(get_db)):
    new_lleidahacker = ModelLleidaHacker(name=payload.name, 
                         email=payload.email,
                         password=payload.password,
                         nickname=payload.nickname,
                         birthdate = payload.birthdate,
                         food_restrictions=payload.food_restrictions,
                         telephone=payload.telephone,
                         address=payload.address,
                         shirt_size=payload.shirt_size)
    db.add(new_lleidahacker)
    db.commit()
    return {"success": True, "created_id": new_lleidahacker.id}

@app.delete("/lleidahacker/{userId}", tags=["LleidaHacker"])
# async def deleteUser(userId:int, response: Response, token: str = Depends(token_auth_scheme)) -> int:
async def delete_lleidahacker(userId:int, response: Response, db: Session = Depends(get_db)):
    # result = VerifyToken(token.credentials).verify()
    # if result.get("status"):
    #    response.status_code = status.HTTP_400_BAD_REQUEST
    #    return result
    db.query(ModelLleidaHacker).filter(ModelLleidaHacker.id == userId).delete()
    db.query(ModelUser).filter(ModelUser.id == userId).delete()
    return {"success": True}

@app.get("/lleidahacker/groups", tags=["LleidaHacker"])
async def get_lleidahacker_groups(db: Session = Depends(get_db)):
    return db.query(ModelLleidaHackerGroup).all()

@app.get("/lleidahacker/group/{groupId}", tags=["LleidaHacker"])
async def get_lleidahacker_group(groupId: int, response: Response, db: Session = Depends(get_db)):
    return db.query(ModelLleidaHackerGroup).filter(ModelLleidaHackerGroup.id == groupId).first()

@app.post("/lleidahacker/group", tags=["LleidaHacker"])
async def add_lleidahacker_group(payload:SchemaLleidaHackerGroup, response: Response, db: Session = Depends(get_db)):
    new_lleidahacker_group = ModelLleidaHackerGroup(name=payload.name, 
                         email=payload.email,
                         password=payload.password,
                         nickname=payload.nickname,
                         birthdate = payload.birthdate,
                         food_restrictions=payload.food_restrictions,
                         telephone=payload.telephone,
                         address=payload.address,
                         shirt_size=payload.shirt_size)
    db.add(new_lleidahacker_group)
    db.commit()
    return {"success": True, "created_id": new_lleidahacker_group.id}

@app.delete("/lleidahacker/group/{groupId}", tags=["LleidaHacker"])
async def delete_lleidahacker_group(groupId:int, response: Response, db: Session = Depends(get_db)):
    # result = VerifyToken(token.credentials).verify()
    # if result.get("status"):
    #    response.status_code = status.HTTP_400_BAD_REQUEST
    #    return result
    db.query(ModelLleidaHackerGroup).filter(ModelLleidaHackerGroup.id == groupId).delete()
    return {"success": True}

@app.get("/lleidahacker/group/{groupId}/members", tags=["LleidaHacker"])
async def get_lleidahacker_group_members(groupId: int, response: Response, db: Session = Depends(get_db)):
    return db.query(ModelLleidaHackerGroup).filter(ModelLleidaHackerGroup.id == groupId).first().members




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
