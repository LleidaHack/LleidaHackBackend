from typing import List

from sqlalchemy import Boolean, Column, Integer, String
from sqlmodel import Field, SQLModel


class UserConfig(SQLModel, table=True):
    __tablename__ = 'user_config'
    id: int = Field(primary_key=True,
                     index=True,
                     unique=True)
    #user_id = Column(Integer, ForeignKey('my_user.id'), nullable=False)
    recive_notifications: bool = Field(default=True)
    default_lang: str = Field(default="ca-CA")
    comercial_notifications: bool = Field(default=True)
    terms_and_conditions: bool = Field(default=True)
