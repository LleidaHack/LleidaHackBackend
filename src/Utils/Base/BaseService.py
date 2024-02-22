from database import db_get


class BaseService:

    def __init__(self):
        self.db = db_get()
