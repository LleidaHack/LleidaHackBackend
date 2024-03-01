from datetime import date
from sqlalchemy import Column, DateTime, Integer, String, Boolean, ForeignKey
from database import Base
from sqlalchemy.orm import deferred
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped



class User(Base):
    __tablename__ = 'user'
    id: int = Column(Integer, primary_key=True, index=True) 
    is_verified: bool = Column(Boolean, default=False)
    token: Mapped[str] = deferred(Column(String, default=""))
    refresh_token: Mapped[str] = deferred(Column(String, default=""))
    verification_token: Mapped[str] = deferred(Column(String, default=""))
    rest_password_token: Mapped[str] = deferred(Column(String, default=""))
    name: str = Column(String)
    nickname: str = Column(String, unique=True, index=True)
    password: Mapped[str] = deferred(Column(String))
    birthdate: date = Column(DateTime)
    food_restrictions: Mapped[str] = deferred(Column(String))
    email: Mapped[str] = deferred(Column(String, unique=True, index=True))
    telephone: Mapped[str] = deferred(Column(String, unique=True, index=True))
    address: Mapped[str] = deferred(Column(String))
    shirt_size: Mapped[str] = deferred(Column(String))
    type: str = Column(String)
    created_at: date = Column(DateTime, default=date.today())
    updated_at: date = Column(DateTime, default=date.today())
    image: str = Column(String, default="")
    is_image_url: bool = Column(Boolean, default=False)
    code: Mapped[str] = deferred(
        Column(String, default="", unique=True, index=True))
    terms_accepted: bool = Column(Boolean, default=True)
    recive_mails: bool = Column(Boolean, default=True)
    lleidacoins_claimed: Boolean = Column(Boolean, default=False)
    config_id = Column(Integer, ForeignKey('user-config.id'))
    config = relationship('UserConfig', foreign_keys=[config_id], backref='user', uselist=False)

    __mapper_args__ = {
        "polymorphic_identity": "user",
        "polymorphic_on": type,
    }



