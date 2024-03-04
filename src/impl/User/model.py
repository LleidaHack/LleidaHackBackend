from datetime import date

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import Mapped, deferred

from src.utils.database import Base


class User(Base):
    __tablename__ = 'user'
    id: int = Column(Integer, primary_key=True, index=True)
    is_verified: bool = Column(Boolean, default=False)

    name: str = Column(String)
    nickname: str = Column(String, unique=True, index=True)
    password: str = (Column(String))
    birthdate: date = Column(DateTime)
    food_restrictions: str = (Column(String))
    email: str = (Column(String, unique=True, index=True))
    telephone: str = Column(String, unique=True, index=True)
    address: str = (Column(String))
    shirt_size: str = (Column(String))
    type: str = Column(String)
    created_at: date = Column(DateTime, default=date.today())
    updated_at: date = Column(DateTime, default=date.today())
    image: str = Column(String, default="")
    is_image_url: bool = Column(Boolean, default=False)
    code: str = (Column(String, default="", unique=True, index=True))
    terms_accepted: bool = Column(Boolean, default=True)
    recive_mails: bool = Column(Boolean, default=True)
    lleidacoins_claimed: Boolean = Column(Boolean, default=False)

    token: str = (Column(String, default=""))
    refresh_token: str = (Column(String, default=""))
    verification_token: str = (Column(String, default=""))
    rest_password_token: str = (Column(String, default=""))

    __mapper_args__ = {
        "polymorphic_identity": "user",
        "polymorphic_on": type,
    }
