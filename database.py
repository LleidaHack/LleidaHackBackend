from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
# from sqlalchemy_utils import database_exists, create_database
from config import Configuration

# engine = create_engine(Configuration.get("POSTGRESQL", "DATABASE_URL"))
# if not database_exists(engine.url):
# create_database(engine.url)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    '''returns the connetion to database'''
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.close()
    finally:
        db.close()


def db_get():
    return SessionLocal()
