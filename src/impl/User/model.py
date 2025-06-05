from datetime import date
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, backref

from src.impl.UserConfig.model import UserConfig
from src.utils.Base.BaseModel import BaseModel


class User(BaseModel):
    __tablename__ = 'my_user'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    name: Mapped[Optional[str]] = mapped_column(String)
    nickname: Mapped[Optional[str]] = mapped_column(String,
                                                    unique=True,
                                                    index=True)
    password: Mapped[Optional[str]] = mapped_column(String)
    birthdate: Mapped[Optional[date]] = mapped_column(DateTime)
    food_restrictions: Mapped[Optional[str]] = mapped_column(String)
    email: Mapped[Optional[str]] = mapped_column(String,
                                                 unique=True,
                                                 index=True)
    telephone: Mapped[Optional[str]] = mapped_column(String,
                                                     unique=True,
                                                     index=True)
    address: Mapped[Optional[str]] = mapped_column(String)
    shirt_size: Mapped[Optional[str]] = mapped_column(String)
    type: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[Optional[date]] = mapped_column(DateTime,
                                                       default=date.today())
    updated_at: Mapped[Optional[date]] = mapped_column(DateTime,
                                                       default=date.today())
    image: Mapped[str] = mapped_column(String, default="")
    # is_image_url: bool = mapped_column(Boolean, default=False)
    code: Mapped[str] = mapped_column(String,
                                      default="",
                                      unique=True,
                                      index=True)
    # terms_accepted: bool = mapped_column(Boolean, default=True)
    # recive_mails: bool = mapped_column(Boolean, default=True)
    # lleidacoins_claimed: Boolean = mapped_column(Boolean, default=False)
    config_id: Mapped[Optional[int]] = mapped_column(Integer,
                                                     ForeignKey(UserConfig.id))
    config: Mapped[Optional["UserConfig"]] = relationship(
        'UserConfig',
        foreign_keys=[config_id],
        backref=backref('user', cascade='all, delete-orphan'),
        uselist=False)
    token: Mapped[str] = mapped_column(String, default="")
    refresh_token: Mapped[str] = mapped_column(String, default="")
    verification_token: Mapped[str] = mapped_column(String, default="")
    rest_password_token: Mapped[str] = mapped_column(String, default="")

    __mapper_args__ = {
        "polymorphic_identity": "my_user",
        "polymorphic_on": type,
    }
