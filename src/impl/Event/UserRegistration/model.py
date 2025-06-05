from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.utils.Base.BaseModel import BaseModel


class UserRegistration(BaseModel):
    __tablename__ = "user_event_registration"
    user_id: Mapped[int] = mapped_column(ForeignKey("my_user.id"),
                                         primary_key=True,
                                         index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("event.id"),
                                          primary_key=True,
                                          index=True)
    shirt_size: Mapped[str] = mapped_column(String)
    food_restrictions: Mapped[str] = mapped_column(String)
    cv: Mapped[Optional[str]] = mapped_column(String)
    description: Mapped[str] = mapped_column(String, default="")
    github: Mapped[str] = mapped_column(String, default="")
    linkedin: Mapped[str] = mapped_column(String, default="")
    studies: Mapped[str] = mapped_column(String, default="")
    study_center: Mapped[str] = mapped_column(String, default="")
    location: Mapped[str] = mapped_column(String, default="")
    how_did_you_meet_us: Mapped[str] = mapped_column(String, default="")
    update_user: Mapped[bool] = mapped_column(Boolean, default=True)
    confirmed_assistance: Mapped[bool] = mapped_column(Boolean, default=False)
    confirm_assistance_token: Mapped[str] = mapped_column(String, default="")
    # accepted: Mapped[bool] = mapped_column(Boolean, default=False)
