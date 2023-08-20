from models.Company import CompanyUser as ModelCompanyUser
from models import TokenData
from schemas.Company import CompanyUser as SchemaCompanyUser

from sqlalchemy.orm import Session

from security import get_password_hash


async def get_all(db: Session):
    return db.query(ModelCompanyUser).all()


async def get_company_user(companyUserId: int, db: Session):
    return db.query(ModelCompanyUser).filter(
        ModelCompanyUser.id == companyUserId).first()


async def add_company_user(payload: SchemaCompanyUser, db: Session):
    new_company_user = ModelCompanyUser(**payload.dict(),
                                        password_hash=get_password_hash(
                                            payload.password))
    db.add(new_company_user)
    db.commit()
    db.refresh(new_company_user)
    return new_company_user


async def update_company_user(payload: SchemaCompanyUser, companyUserId: int,
                              db: Session, data: TokenData):
    if not data.is_admin:
        if not data.available or not (data.type == "lleida_hacker" or
                                      (data.type == "company_user"
                                       and data.user_id != companyUserId)):
            raise Exception("Not authorized")
    company_user = db.query(ModelCompanyUser).filter(
        ModelCompanyUser.id == companyUserId).first()
    if not company_user:
        raise Exception("Company user not found")

    company_user.name = payload.name
    company_user.nickname = payload.nickname
    company_user.birthdate = payload.birthdate
    company_user.address = payload.address
    company_user.telephone = payload.telephone
    company_user.shirt_size = payload.shirt_size
    company_user.food_restrictions = payload.food_restrictions
    company_user.image_id = payload.image_id
    # company_user.company_id = payload.company_id
    company_user.role = payload.role
    db.commit()
    db.refresh(company_user)
    return company_user


async def delete_company_user(companyUserId: int, db: Session,
                              data: TokenData):
    if not data.is_admin:
        if not data.available or not (data.type == "lleida_hacker" or
                                      (data.type == "company_user"
                                       and data.user_id != companyUserId)):
            raise Exception("Not authorized")
    company_user = db.query(ModelCompanyUser).filter(
        ModelCompanyUser.id == companyUserId).first()
    db.delete(company_user)
    db.commit()
    return company_user
