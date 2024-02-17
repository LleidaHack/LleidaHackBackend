from database import get_db


class BaseService:

    def __init__(self):
        self.model = get_db()
