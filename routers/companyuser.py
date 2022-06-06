from models.Company import CompanyUser as ModelCompanyUser
from models.User import User as ModelUser

from schemas.Company import CompanyUser as SchemaCompanyUser

from database import get_db
from security import create_access_token, get_password_hash, oauth_schema

from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

router = APIRouter(
    prefix="/company/user",
    tags=["Company User"],
    # dependencies=[Depends(get_db)],
    # dependencies=[Depends(get_token_header)],
    # responses={404: {"description": "Not found"}},
)

@router.post("/signup")
async def signup(payload: SchemaCompanyUser, response: Response, db: Session = Depends(get_db)):
    new_companyuser = ModelCompanyUser(name=payload.name,
                                       email=payload.email,
                                       password=get_password_hash(payload.password),
                                       nickname=payload.nickname,
                                       birthdate=payload.birthdate,
                                       address=payload.address,
                                       telephone=payload.telephone,
                                       shirt_size=payload.shirt_size,
                                       food_restrictions=payload.food_restrictions,
                                       company_id=payload.company_id,
                                       role=payload.role,
    )
    db.add(new_companyuser)
    db.commit()
    token=create_access_token(new_companyuser)
    return {"success": True, "created_id": new_companyuser.id, "token": token}

@router.get("/all")
async def get_company_users(db: Session = Depends(get_db), str = Depends(oauth_schema)):
    return db.query(ModelCompanyUser).all()

@router.get("/{companyUserId}")
async def get_company_user(companyUserId: int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    return db.query(ModelCompanyUser).filter(ModelCompanyUser.id == companyUserId).first()

@router.post("/")
async def add_company_user(payload:SchemaCompanyUser, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    new_company_user = ModelCompanyUser(name=payload.name,
                                        email=payload.email,
                                        password=payload.password,
                                        nickname=payload.nickname,
                                        birthdate=payload.birthdate,
                                        address=payload.address,
                                        telephone=payload.telephone,
                                        shirt_size=payload.shirt_size,
                                        food_restrictions=payload.food_restrictions,

                                        company_id=payload.company_id,
                                        role=payload.role,
    )
    db.add(new_company_user)
    db.commit()
    return {"success": True, "created_id": new_company_user.id}


@router.put("/{companyUserId}")
async def update_company_user(companyUserId: int, payload: SchemaCompanyUser, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    company_user = db.query(ModelCompanyUser).filter(ModelCompanyUser.id == companyUserId).first()
    if company_user:
        company_user.name = payload.name
        company_user.email = payload.email
        company_user.password = payload.password
        company_user.nickname = payload.nickname
        company_user.birthdate = payload.birthdate
        company_user.address = payload.address
        company_user.telephone = payload.telephone
        company_user.shirt_size = payload.shirt_size
        company_user.food_restrictions = payload.food_restrictions
        company_user.company_id = payload.company_id
        company_user.role = payload.role
        db.commit()
        return {"success": True}
    else:
        return {"success": False}

@router.delete("/{companyUserId}")
async def delete_company_user(companyUserId: int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    company_user = db.query(ModelCompanyUser).filter(ModelCompanyUser.id == companyUserId).first()
    if company_user:
        db.delete(company_user)
        db.commit()
        return {"success": True}
    else:
        return {"success": False}
