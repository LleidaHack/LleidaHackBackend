from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship

from database import Base

class Notification(Base):
    __tablename__ = 'notification'
    id: int = Column(Integer, primary_key=True, index=True)
    user_id: int = Column(Integer, ForeignKey('user.id'))
    message: str = Column(String)
    read: bool = Column(Boolean, default=False)
    created_at: str = Column(String)
    updated_at: str = Column(String)
    deleted_at: str = Column(String)