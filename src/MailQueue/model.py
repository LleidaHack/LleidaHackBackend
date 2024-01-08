from __future__ import annotations
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship
from database import Base

from sqlalchemy.orm import deferred
from sqlalchemy.orm import Mapped


class MailQueue(Base):
    __tablename__ = "mail_queue"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"))

    subject = Column(String, index=True)
    body = Column(String, index=True)
    sent = Column(Boolean, default=False)

    user = relationship("User")
