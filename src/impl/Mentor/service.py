from fastapi_sqlalchemy import db
from src.utils.Base.BaseService import BaseService


class MentorService(BaseService):

    def _get_by_id(self, id: int):
        out = db.session.query(MentorModel).filter(
            MentorModel.id == id).first()
        if out is None:
            raise
        return out
