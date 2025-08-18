from __future__ import annotations

from datetime import datetime
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.utils.Base.BaseModel import BaseModel


class Activity(BaseModel):
    __tablename__ = "activity"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    edition: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    sponsor: Mapped[str] = mapped_column(String(200), nullable=True)     # New
    location: Mapped[str] = mapped_column(String(200), nullable=True)    # New
    day_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
