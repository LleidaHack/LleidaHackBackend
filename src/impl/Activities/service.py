from fastapi_sqlalchemy import db

from src.error.AuthenticationException import AuthenticationException
from src.error.NotFoundException import NotFoundException
from src.impl.Activity.model import Activity
from src.impl.Activity.schema import ActivityCreate, ActivityUpdate
from src.utils.Base.BaseService import BaseService
from src.utils.service_utils import set_existing_data
from src.utils.Token import BaseToken
from src.utils.UserType import UserType


class ActivityService(BaseService):
    name = "activity_service"

    def get_all(self):
        return db.session.query(Activity).all()

    def get_by_id(self, activity_id: int):
        activity = db.session.query(Activity).filter(Activity.id == activity_id).first()
        if activity is None:
            raise NotFoundException("activity not found")
        return activity

    def create(self, activity: ActivityCreate, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("You are not allowed to add activities")
        db_activity = Activity(**activity.model_dump())
        db.session.add(db_activity)
        db.session.commit()
        db.session.refresh(db_activity)
        return db_activity

    def update(self, id: int, activity: ActivityUpdate, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("You are not allowed to update activities")
        db_activity = self.get_by_id(id)
        set_existing_data(db_activity, activity)
        db.session.commit()
        db.session.refresh(db_activity)
        return db_activity

    def delete(self, id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("You are not allowed to delete activities")
        db_activity = self.get_by_id(id)
        db.session.delete(db_activity)
        db.session.commit()
        return db_activity
