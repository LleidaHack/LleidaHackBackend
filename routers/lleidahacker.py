from models.User import User as ModelUser
from models.LleidaHacker import LleidaHacker as ModelLleidaHacker
from models.LleidaHacker import LleidaHackerGroup as ModelLleidaHackerGroup


from schemas.LleidaHacker import LleidaHacker as SchemaLleidaHacker

from database import get_db
from security import create_access_token, get_password_hash, oauth_schema

from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

router = APIRouter(
    prefix="/lleidahacker",
    tags=["LleidaHacker"],
    # dependencies=[Depends(get_db)],
    # dependencies=[Depends(get_token_header)],
    # responses={404: {"description": "Not found"}},
)

@router.post("/signup")
async def signup(payload: SchemaLleidaHacker, response: Response, db: Session = Depends(get_db)):
    new_lleidahacker = ModelLleidaHacker(name=payload.name, 
                                         email=payload.email,
                                         password=get_password_hash(payload.password),
                                         nickname=payload.nickname,
                                         birthdate = payload.birthdate,
                                         food_restrictions=payload.food_restrictions,
                                         telephone=payload.telephone,
                                         address=payload.address,
                                         shirt_size=payload.shirt_size,
                                         nif=payload.nif,
                                         student=payload.student,
                                         role=payload.role,
                                         #   group=payload.group,
                                         active=payload.active,
                                         image=payload.image,
                                         github=payload.github
    )
    db.add(new_lleidahacker)
    db.commit()
    token=create_access_token(new_lleidahacker)
    return {"success": True, "created_id": new_lleidahacker.id, "token": token}

@router.get("/all")
async def get_lleidahacker(db: Session = Depends(get_db), str = Depends(oauth_schema)):
    return db.query(ModelLleidaHacker).all()

@router.get("/{userId}")
async def get_lleidahacker(userId: int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    return db.query(ModelLleidaHacker).filter(ModelLleidaHacker.id == userId).first()

@router.post("/")
async def add_lleidahacker(payload:SchemaLleidaHacker, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
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

@router.delete("/{userId}")
# async def deleteUser(userId:int, response: Response, token: str = Depends(token_auth_scheme)) -> int:
async def delete_lleidahacker(userId:int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    # result = VerifyToken(token.credentials).verify()
    # if result.get("status"):
    #    response.status_code = status.HTTP_400_BAD_REQUEST
    #    return result
    db.query(ModelLleidaHacker).filter(ModelLleidaHacker.id == userId).delete()
    db.query(ModelUser).filter(ModelUser.id == userId).delete()
    return {"success": True}

@router.put("/{userId}")
async def update_lleidahacker(userId:int, payload: SchemaLleidaHacker, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    # result = VerifyToken(token.credentials).verify()
    # if result.get("status"):
    #    response.status_code = status.HTTP_400_BAD_REQUEST
    #    return result
    db.query(ModelLleidaHacker).filter(ModelLleidaHacker.id == userId).update(payload)
    return {"success": True}
