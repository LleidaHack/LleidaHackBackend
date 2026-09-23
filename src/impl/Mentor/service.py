from fastapi_sqlalchemy import db

from src.error.NotFoundException import NotFoundException
from src.impl.Mentor.model import Mentor
from src.utils.Base.BaseService import BaseService


class MentorService(BaseService):
    def _get_by_id(self, id: int):
        out = db.session.query(Mentor).filter(Mentor.id == id).first()
        if out is None:
            raise NotFoundException("Mentor not found")
        return out
