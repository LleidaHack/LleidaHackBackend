from Models import User as ModelUser
from schema import User as SchemaUser
from database import get_db

from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter, status

# from fastapi import Depends, FastAPI, Response Request
from fastapi.security import HTTPBearer
from utils import VerifyToken

jwt_handdler=VerifyToken()

router = APIRouter(
    prefix="/user",
    tags=["User"],
    # dependencies=[Depends(get_db)],
    # dependencies=[Depends(get_token_header)],
    # responses={404: {"description": "Not found"}},
)

token_auth_scheme = HTTPBearer()

@router.post("/signup")
async def signup(payload: SchemaUser, response: Response, db: Session = Depends(get_db)):
    new_user = ModelUser(name=payload.name, 
                        email=payload.email,
                        password=payload.password,
                        nickname=payload.nickname,
                        birthdate = payload.birthdate,
                        food_restrictions=payload.food_restrictions,
                        telephone=payload.telephone,
                        address=payload.address,
                        shirt_size=payload.shirt_size)
    db.add(new_user)
    db.commit()
    token=jwt_handdler.create_token(new_user.email)
    return {"success": True, "created_id": new_user.id, "token": token}


@router.get("/all")
async def get_users(db: Session = Depends(get_db)):
    return db.query(ModelUser).all()

@router.get("/{userId}")
# async def getUser(userId: int, response: Response, token: str = Depends(token_auth_scheme)):
async def get_user(userId: int, response: Response, db: Session = Depends(get_db), token: str = Depends(token_auth_scheme)):
    result = VerifyToken(token.credentials).verify()
    if result.get("status"):
       response.status_code = status.HTTP_400_BAD_REQUEST
       return result
    return db.query(ModelUser).filter(ModelUser.id == userId).first()

@router.post("/")
# async def addUser(payload:User, response: Response, token: str = Depends(token_auth_scheme)) -> int:
async def add_user(payload:SchemaUser, response: Response, db: Session = Depends(get_db)):
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
                         shirt_size=payload.shirt_size)
    db.add(new_user)
    db.commit()
    # db.refresh(new_job)
    return {"success": True, "created_id": new_user.id}
    # return service.addUser(payload)

@router.put("/{userId}")
# async def updateUser(userId: int, payload: User, response: Response, token: str = Depends(token_auth_scheme)):
async def update_user(userId: int, payload: SchemaUser, response: Response, db: Session = Depends(get_db)):
    # result = VerifyToken(token.credentials).verify()
    # if result.get("status"):
    #    response.status_code = status.HTTP_400_BAD_REQUEST
    #    return result
    user = db.query(ModelUser).filter(ModelUser.id == userId).first()
    user.name = payload.name
    user.email = payload.email
    user.password = payload.password
    user.nickname = payload.nickname
    user.birthdate = payload.birthdate
    user.food_restrictions = payload.food_restrictions
    user.telephone = payload.telephone
    user.address = payload.address
    user.shirt_size = payload.shirt_size
    db.commit()

@router.delete("/{userId}")
# async def removeUser(userId:int, response: Response, token: str = Depends(token_auth_scheme)) -> int:
async def remove_user(userId:int, response: Response, db: Session = Depends(get_db)):
#     result = VerifyToken(token.credentials).verify()
#     if result.get("status"):
#        response.status_code = status.HTTP_400_BAD_REQUEST
#        return result
    return db.query(ModelUser).filter(ModelUser.id == userId).delete()