from typing import Optional, TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.utils.Base.BaseModel import BaseModel

if TYPE_CHECKING:
    from src.impl.User.model import User


class UserConfig(BaseModel):
    __tablename__ = "user_config"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, autoincrement=True
    )
    recive_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    default_lang: Mapped[str] = mapped_column(String, default="ca-CA")
    comercial_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    terms_and_conditions: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationship back to User (one-to-one)
    user: Mapped[Optional["User"]] = relationship("User", back_populates="config")
