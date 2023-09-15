from datetime import date
from sqlalchemy import Column, DateTime, Integer, String, Boolean, Text
from database import Base
# from passlib import hash
from sqlalchemy.orm import deferred

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class User(Base):
    __tablename__ = 'user'
    id: int = Column(Integer, primary_key=True, index=True)
    token: Mapped[str] = deferred(Column(Text, default=""))
    refresh_token: Mapped[str] = deferred(Column(String, default=""))
    name: str = Column(String)
    nickname: str = Column(String)
    password: Mapped[str] = deferred(Column(String))
    birthdate: date = Column(DateTime)
    food_restrictions: Mapped[str] = deferred(Column(String))
    email: Mapped[str] = deferred(Column(String, unique=True))
    telephone: Mapped[str] = deferred(Column(String))
    address: Mapped[str] = deferred(Column(String))
    shirt_size: Mapped[str] = deferred(Column(String))
    type: str = Column(String)
    created_at: date = Column(DateTime, default=date.today())
    updated_at: date = Column(DateTime, default=date.today())
    image: str = Column(String, default="")
    is_image_url: bool = Column(Boolean, default=False)
    code: Mapped[str] = deferred(Column(String, default="", unique=True, index=True))

    __mapper_args__ = {
        "polymorphic_identity": "user",
        "polymorphic_on": type,
    }
    # __allow_unmapped__ = True

    # def verify_password(self, password):
    # return hash.verify(password, self.password)
