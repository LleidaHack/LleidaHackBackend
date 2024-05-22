from sqlalchemy import Column, ForeignKey, String

from src.utils.Base.BaseModel import BaseModel


class UserGeocaching(BaseModel):
    __tablename__ = 'user_geocaching'
    user_code = Column(String, ForeignKey('my_user.code'), primary_key=True)
    code = Column(String, ForeignKey('geocaching.code'), primary_key=True)


class Geocaching(BaseModel):
    __tablename__ = 'geocaching'
    code = Column(String, primary_key=True, index=True)
    name = Column(String)
