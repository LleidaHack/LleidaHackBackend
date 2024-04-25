from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# from sqlalchemy_utils import database_exists, create_database
from src.configuration.Configuration import Configuration
from src.utils.Singleton import Singleton

Base = declarative_base()

# engine = create_engine(Configuration.database.url)
# SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)


# if not database_exists(engine.url):
# def db_get():
#     return SessionLocal()


# class Database(metaclass=Singleton):

#     # def __init__(self):
#     # engine = create_engine(
#     #         Configuration.get("POSTGRESQL", "DATABASE_URL"))
#     # SessionLocal = sessionmaker(autocommit=True,
#     #                                      autoflush=True,
#     #                                      bind=engine)
#     # db = SessionLocal()
#     # if not database_exists(engine.url):
#     # create_database(engine.url)

#     def get_db(self):
#         '''returns the connetion to database'''
#         try:
#             yield Database.db
#         except Exception as e:
#             Database.db.close()
#         finally:
#             Database.db.close()


# # @contextmanager
# def db_get():
#     db = Database.SessionLocal()
#     # return Database.db
#     try:
#         yield db
#     except Exception as e:
#         db.close()
#         raise
#     finally:
#         db.close()
# return self.SessionLocal()
