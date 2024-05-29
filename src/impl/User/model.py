from datetime import date

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, backref
from sqlmodel import Relationship, SQLModel, Field

from src.impl.UserConfig.model import UserConfig
from src.utils.Base.BaseModel import BaseModel


class User(SQLModel, table = True):
    __tablename__ = 'my_user'
    id: int = Field(primary_key=True, index=True)
    is_verified: bool = Field(default=False)
    is_deleted: bool = Field(default=False)
    name: str
    nickname: str = Field(unique=True, index=True)
    password: str
    birthdate: date
    food_restrictions: str
    email: str = Field(unique=True, index=True)
    telephone: str = Field(unique=True, index=True)
    address: str
    shirt_size: str
    type: str
    created_at: date = Field(default=date.today())
    updated_at: date = Field(default=date.today())
    image: str = Field(default="")
    # is_image_url: bool = Column(Boolean, default=False)
    code: str = Field(default="", unique=True, index=True)
    config_id: int = Field(foreign_key = 'user_config.id')
    # config: 'UserConfig' = Relationship(foreign_keys=[config_id],backref=backref('user',cascade='all, delete-orphan'),uselist=False)
    # config: 'UserConfig' = Relationship(back_populates='user',sa_relationship_kwargs={'foreign_keys': [config_id]})
    token: str = Field(default="")
    refresh_token: str = Field(default="")
    verification_token: str = Field(default="")
    rest_password_token: str = Field(default="")

    __mapper_args__ = {
        "polymorphic_identity": "my_user",
        "polymorphic_on": 'type',
    }
