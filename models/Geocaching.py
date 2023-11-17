from datetime import date
from typing import List

# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.orm import deferred
from sqlalchemy.orm import Mapped

from database import Base

class UserGeocaching(Base):
    __tablename__ = 'user_geocaching'
    user_code = Column(String, ForeignKey('user.code'), primary_key=True)
    code = Column(String, ForeignKey('geocaching.code'), primary_key=True)

class Geocaching(Base):
    __tablename__ = 'geocaching'
    code = Column(String, primary_key=True, index=True)
    name = Column(String)