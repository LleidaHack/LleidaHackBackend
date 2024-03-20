from __future__ import annotations

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, deferred, relationship

from src.utils.database import Base


class MailQueue(Base):
    __tablename__ = "mail_queue"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("my_user.id"))

    subject = Column(String, index=True)
    body = Column(String, index=True)
    sent = Column(Boolean, default=False)
    user = relationship("User")
