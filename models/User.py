from datetime import date
from sqlalchemy import Column, DateTime, Integer, String, Boolean
from database import Base
# from passlib import hash
from sqlalchemy.orm import deferred


class User(Base):
    __tablename__ = 'user'
    id: int = Column(Integer, primary_key=True, index=True)
    token: str = deferred(Column(String, default=""))
    refresh_token: str = deferred(Column(String, default=""))
    name: str = Column(String)
    nickname: str = Column(String, unique=True, index=True)
    password: str = deferred(Column(String))
    birthdate: date = Column(DateTime)
    food_restrictions: str = deferred(Column(String))
    email: str = deferred(Column(String, unique=True, index=True))
    telephone: str = deferred(Column(String))
    address: str = deferred(Column(String))
    shirt_size: str = deferred(Column(String))
    type: str = Column(String)
    created_at: date = Column(DateTime, default=date.today())
    updated_at: date = Column(DateTime, default=date.today())
    image: str = Column(String, default="")
    is_image_url: bool = Column(Boolean, default=False)
    code: str = deferred(Column(String, default="", unique=True, index=True))

    __mapper_args__ = {
        "polymorphic_identity": "user",
        "polymorphic_on": type,
    }

    # def verify_password(self, password):
    # return hash.verify(password, self.password)
