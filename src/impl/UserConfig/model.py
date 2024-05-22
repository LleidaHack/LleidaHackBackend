from typing import List

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase

from src.utils.Base.BaseModel import BaseModel


class UserConfig(BaseModel):
    __tablename__ = 'user_config'
    id: int = Column(Integer,
                     primary_key=True,
                     index=True,
                     unique=True,
                     autoincrement=True)
    #user_id = Column(Integer, ForeignKey('my_user.id'), nullable=False)
    recive_notifications = Column(Boolean, default=True)
    default_lang = Column(String, default="ca-CA")
    comercial_notifications = Column(Boolean, default=True)
    terms_and_conditions = Column(Boolean, default=True)
