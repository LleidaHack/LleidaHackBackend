from typing import List
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Enum
from sqlalchemy.orm import relationship


from models.User import User as ModelUser

from database import Base
import enum

class RoleEnum(enum.Enum):
    Admin = 0
    User = 1
    Guest = 2


class Role(Base):
    __tablename__ = 'role'
    id: int = Column(Integer, primary_key=True, index=True)
    name = Column(Enum(RoleEnum), index=True)
    # description: str = Column(String)
    users: List[ModelUser] = relationship('User', back_populates='roles')