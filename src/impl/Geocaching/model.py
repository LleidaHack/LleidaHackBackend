from datetime import date
from sqlalchemy import Column, ForeignKey, String

from src.utils.database import Base


class UserGeocaching(Base):
    __tablename__ = 'user_geocaching'
    user_code = Column(String, ForeignKey('user.code'), primary_key=True)
    code = Column(String, ForeignKey('geocaching.code'), primary_key=True)


class Geocaching(Base):
    __tablename__ = 'geocaching'
    code = Column(String, primary_key=True, index=True)
    name = Column(String)
