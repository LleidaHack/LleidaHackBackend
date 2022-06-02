import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from sqlalchemy_utils import database_exists, create_database

load_dotenv('.env')
SQLALCHEMY_DATABASE_URL =  os.environ.get("DATABASE_URL")
engine = create_engine ( SQLALCHEMY_DATABASE_URL )
if not database_exists(engine.url):
    create_database(engine.url)
SessionLocal = sessionmaker ( autocommit = False , autoflush = False , bind = engine )
Base = declarative_base ( )

def get_db() :
    db = SessionLocal ( )
    try :
        yield db
    except :
        db.close ( )