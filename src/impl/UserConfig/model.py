from typing import List

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String

from src.utils.database import Base


class UserConfig(Base):
    __tablename__ = 'user_config'
    id: int = Column(Integer,
                     primary_key=True,
                     index=True,
                     unique=True,
                     autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    reciveNotifications = Column(Boolean, default=True)
    defaultLang = Column(String, default="ca-CA")
    comercialNotifications = Column(Boolean, default=True)
