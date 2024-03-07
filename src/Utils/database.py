from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# from sqlalchemy_utils import database_exists, create_database
from src.utils.Configuration import Configuration
from src.utils.Singleton import Singleton

Base = declarative_base()


class Database(metaclass=Singleton):

    def __init__(self):
        self.engine = create_engine(
            Configuration.get("POSTGRESQL", "DATABASE_URL"))
        self.SessionLocal = sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=self.engine)
        # if not database_exists(engine.url):
        # create_database(engine.url)

    def get_db(self):
        '''returns the connetion to database'''
        db = self.SessionLocal()
        try:
            yield db
        except Exception as e:
            db.close()
        finally:
            db.close()

    def db_get(self):
        return self.SessionLocal()
