from fastapi_sqlalchemy import db

from src.impl.Mentor.model import Mentor
from src.utils.Base.BaseService import BaseService


class MentorService(BaseService):
    def _get_by_id(self, item_id: int):
        out = db.session.query(Mentor).filter(Mentor.id == id).first()
        if out is None:
            raise
        return out
