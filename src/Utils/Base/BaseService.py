from src.utils.database import db_get
# from typing import List, TypeVar, Generic

# T = TypeVar('T')

# class GBaseService(Generic[T]):
#     def __init__(self):
#         self.db = db_get()

#     def get_by_id(self, id:int):
#         return self.db.query(T).filter(T.id == id).first()
    
#     def get_all(self):
#         return self.db.query(self.model).all()

class BaseService:

    def __init__(self):
        self.db = db_get()
  
    @classmethod
    def get_all(cls):
        return cls.db.query(cls.model).all()
  
    @classmethod
    def get_by_id(cls):
        return cls.model.query.filter(...)