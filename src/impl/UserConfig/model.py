from sqlalchemy import Boolean, String, false
from sqlalchemy.orm import Mapped, mapped_column

from src.utils.Base.BaseModel import BaseModel


class UserConfig(BaseModel):
    __tablename__ = "user_config"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, autoincrement=True
    )
    # user_id = Column(Integer, ForeignKey('my_user.id'), nullable=False)
    recive_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    default_lang: Mapped[str] = mapped_column(String, default="ca-CA")
    comercial_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    terms_and_conditions: Mapped[bool] = mapped_column(Boolean, default=True)
    mlh_code_of_conduct: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false(), nullable=False
    )
    # # Relationship back to User (one-to-one)
    # # user: Mapped[Optional["User"]] = relationship("User", back_populates="config")
