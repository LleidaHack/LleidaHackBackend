from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.utils.Base.BaseModel import BaseModel


class UserGeocaching(BaseModel):
    __tablename__ = 'user_geocaching'
    user_code: Mapped[str] = mapped_column(
        String, ForeignKey('my_user.code'), primary_key=True
    )
    code: Mapped[str] = mapped_column(
        String, ForeignKey('geocaching.code'), primary_key=True
    )


class Geocaching(BaseModel):
    __tablename__ = 'geocaching'
    code: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String)
