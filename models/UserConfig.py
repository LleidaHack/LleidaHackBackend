from typing import List
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base
from models.User import User
from models.UserType import UserType
from schemas.Event import Event



class UserConfig(Base):
    __tablename__ = 'user-config'
    id: int = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    ##user = relationship('user', backref = 'config')
    reciveNotifications = Column(Boolean, default=True)
    defaultLang = Column(String, default="ca-CA")
    comercialNotifications = Column(Boolean, default=True)





