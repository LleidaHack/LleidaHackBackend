from Models import User as ModelUser
from Models import LleidaHacker as ModelLleidaHacker
from Models import LleidaHackerGroup as ModelLleidaHackerGroup


from schema import LleidaHacker as SchemaLleidaHacker
from schema import LleidaHackerGroup as SchemaLleidaHackerGroup

from database import get_db

from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

router = APIRouter(
    prefix="/lleidahacker",
    tags=["LleidaHacker"],
    # dependencies=[Depends(get_db)],
    # dependencies=[Depends(get_token_header)],
    # responses={404: {"description": "Not found"}},
)

@router.get("/all")
async def get_lleidahacker(db: Session = Depends(get_db)):
    return db.query(ModelLleidaHacker).all()

@router.get("/{userId}")
async def get_lleidahacker(userId: int, response: Response, db: Session = Depends(get_db)):
    return db.query(ModelLleidaHacker).filter(ModelLleidaHacker.id == userId).first()

@router.post("")
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

@router.delete("/{userId}")
# async def deleteUser(userId:int, response: Response, token: str = Depends(token_auth_scheme)) -> int:
async def delete_lleidahacker(userId:int, response: Response, db: Session = Depends(get_db)):
    # result = VerifyToken(token.credentials).verify()
    # if result.get("status"):
    #    response.status_code = status.HTTP_400_BAD_REQUEST
    #    return result
    db.query(ModelLleidaHacker).filter(ModelLleidaHacker.id == userId).delete()
    db.query(ModelUser).filter(ModelUser.id == userId).delete()
    return {"success": True}

@router.get("/groups")
async def get_lleidahacker_groups(db: Session = Depends(get_db)):
    return db.query(ModelLleidaHackerGroup).all()

@router.get("/group/{groupId}")
async def get_lleidahacker_group(groupId: int, response: Response, db: Session = Depends(get_db)):
    return db.query(ModelLleidaHackerGroup).filter(ModelLleidaHackerGroup.id == groupId).first()

@router.post("/group")
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

@router.delete("/group/{groupId}")
async def delete_lleidahacker_group(groupId:int, response: Response, db: Session = Depends(get_db)):
    # result = VerifyToken(token.credentials).verify()
    # if result.get("status"):
    #    response.status_code = status.HTTP_400_BAD_REQUEST
    #    return result
    db.query(ModelLleidaHackerGroup).filter(ModelLleidaHackerGroup.id == groupId).delete()
    return {"success": True}

@router.get("/group/{groupId}/members")
async def get_lleidahacker_group_members(groupId: int, response: Response, db: Session = Depends(get_db)):
    return db.query(ModelLleidaHackerGroup).filter(ModelLleidaHackerGroup.id == groupId).first().members