"""coding=utf-8."""
 
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
 
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:pass@host:port/db_name"
 
engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)
 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
 
Base = declarative_base()