from models.User import User as ModelUser
from models.Hacker import Hacker as ModelHacker

from schemas.Hacker import Hacker as SchemaHacker

from database import get_db

from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

from security import create_access_token, get_password_hash, oauth_schema

router = APIRouter(
    prefix="/hacker",
    tags=["Hacker"],
    # dependencies=[Depends(get_db)],
    # dependencies=[Depends(get_token_header)],
    # responses={404: {"description": "Not found"}},
)

@router.post("/signup")
async def signup(payload: SchemaHacker, response: Response, db: Session = Depends(get_db)):
    new_hacker = ModelHacker(name=payload.name, 
                             email=payload.email,
                             password=get_password_hash(payload.password),
                             nickname=payload.nickname,
                             birthdate = payload.birthdate,
                             food_restrictions=payload.food_restrictions,
                             telephone=payload.telephone,
                             address=payload.address,
                             github=payload.github,
                             linkedin=payload.linkedin,
                             shirt_size=payload.shirt_size)
    db.add(new_hacker)
    db.commit()
    token=create_access_token(new_hacker)
    return {"success": True, "created_id": new_hacker.id, "token": token}

@router.get("/all")
async def get_hackers(db: Session = Depends(get_db), str = Depends(oauth_schema)):
    return db.query(ModelHacker).all()

@router.get("/{hackerId}")
async def get_hacker(hackerId: int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    return db.query(ModelHacker).filter(ModelHacker.id == hackerId).first()

@router.post("/")
async def add_hacker(payload:SchemaHacker, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
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

@router.put("/{hackerId}")
async def update_hacker(hackerId: int, payload: SchemaHacker, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
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

@router.post("/{userId}/ban")
# async def banUser(userId:int, response: Response, token: str = Depends(token_auth_scheme)) -> int:
async def ban_hacker(userId:int, db: Session = Depends(get_db), str = Depends(oauth_schema)) -> int:
    # result = VerifyToken(token.credentials).verify()
    # if result.get("status"):
    #    response.status_code = status.HTTP_400_BAD_REQUEST
    #    return result
    if db.query(ModelUser).filter(ModelUser.id == userId).first().type=="hacker":
        return db.query(ModelUser).filter(ModelUser.id == userId).update({"banned":1})
    else:
        return {"success": False}


@router.post("/{userId}/unban")
# async def unbanUser(userId:int, response: Response, token: str = Depends(token_auth_scheme)) -> int:
async def unban_hacker(userId:int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    # result = VerifyToken(token.credentials).verify()
    # if result.get("status"):
    #    response.status_code = status.HTTP_400_BAD_REQUEST
    #    return result
    if db.query(ModelUser).filter(ModelUser.id == userId).first().type=="hacker":
        return db.query(ModelUser).filter(ModelUser.id == userId).update({"banned":0})
    else:
        return {"success": False}

@router.delete("/{userId}")
# async def deleteUser(userId:int, response: Response, token: str = Depends(token_auth_scheme)) -> int:
async def delete_hacker(userId:int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    # result = VerifyToken(token.credentials).verify()
    # if result.get("status"):
    #    response.status_code = status.HTTP_400_BAD_REQUEST
    #    return result
    db.query(ModelHacker).filter(ModelHacker.id == userId).delete()
    db.query(ModelUser).filter(ModelUser.id == userId).delete()
    return {"success": True}

