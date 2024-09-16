from fastapi_sqlalchemy import db
from src.utils.Base.BaseService import BaseService
from src.impl.Mentor.model import Mentor


class MentorService(BaseService):

    def _get_by_id(self, id: int):
        out = db.session.query(Mentor).filter(Mentor.id == id).first()
        if out is None:
            raise
        return out
