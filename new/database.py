from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "postgresql://lleidahack:lleidahackVPSAPI@localhost/new"
engine = create_engine ( SQLALCHEMY_DATABASE_URL )
SessionLocal = sessionmaker ( autocommit = False , autoflush = False , bind = engine )
Base = declarative_base ( )

def get_db() :
    db = Session.Local ( )
    try :
        yield db
    except :
        db.close ( )