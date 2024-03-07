from datetime import datetime as date

from src.error.AuthenticationException import AuthenticationException
from src.error.NotFoundException import NotFoundException
from src.impl.LleidaHacker.model import LleidaHacker as ModelLleidaHacker
from src.impl.LleidaHacker.schema import \
    LleidaHackerCreate as LleidaHackerCreateSchema
from src.impl.LleidaHacker.schema import \
    LleidaHackerGet as LleidaHackerGetSchema
from src.impl.LleidaHacker.schema import \
    LleidaHackerGetAll as LleidaHackerGetAllSchema
from src.impl.LleidaHacker.schema import \
    LleidaHackerUpdate as LleidaHackerUpdateSchema
from src.utils.Base.BaseService import BaseService
from src.utils.security import get_password_hash
from src.utils.service_utils import (check_image, check_user,
                                     generate_user_code, set_existing_data)
from src.utils.Token import BaseToken
from src.utils.UserType import UserType


class LleidaHackerService(BaseService):

    def __call__(self):
        pass

    def get_all(self):
        return self.db.query(ModelLleidaHacker).all()

    def get_by_id(self, id: int):
        user = self.db.query(ModelLleidaHacker).filter(
            ModelLleidaHacker.id == id).first()
        if user is None:
            raise NotFoundException("LleidaHacker not found")
        return user

    def get_lleidahacker(self, userId: int, data: BaseToken):
        user = self.get_by_id(userId)
        if data.check([UserType.LLEIDAHACKER], userId):
            return LleidaHackerGetAllSchema.from_orm(user)
        return LleidaHackerGetSchema.from_orm(user)

    def add_lleidahacker(self, payload: LleidaHackerCreateSchema):
        check_user(payload.email, payload.nickname, payload.telephone)
        if payload.image is not None:
            payload = check_image(payload)
        new_lleidahacker = ModelLleidaHacker(**payload.dict(),
                                             code=generate_user_code())
        new_lleidahacker.password = get_password_hash(payload.password)
        self.db.add(new_lleidahacker)
        self.db.commit()
        self.db.refresh(new_lleidahacker)
        return new_lleidahacker

    def update_lleidahacker(self, userId: int,
                            payload: LleidaHackerUpdateSchema,
                            data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER], userId):
            raise AuthenticationException("Not authorized")
        lleidahacker = self.get_by_id(userId)
        if payload.image is not None:
            payload = check_image(payload)
        updated = set_existing_data(lleidahacker, payload)
        lleidahacker.updated_at = date.now()
        updated.append("updated_at")
        if payload.password is not None:
            lleidahacker.password = get_password_hash(payload.password)
        self.db.commit()
        self.db.refresh(lleidahacker)
        return lleidahacker, updated

    def delete_lleidahacker(self, userId: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER], userId):
            raise AuthenticationException("Not authorized")
        lleidahacker = self.get_by_id(userId)
        self.db.delete(lleidahacker)
        self.db.commit()
        return lleidahacker

    def accept_lleidahacker(self, userId: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        lleidahacker = self.get_by_id(userId)
        lleidahacker.active = 1
        lleidahacker.accepted = 1
        lleidahacker.rejected = 0
        self.db.commit()
        self.db.refresh(lleidahacker)
        return lleidahacker

    def reject_lleidahacker(self, userId: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        lleidahacker = self.get_by_id(userId)
        lleidahacker.active = 0
        lleidahacker.accepted = 0
        lleidahacker.rejected = 1
        self.db.commit()
        self.db.refresh(lleidahacker)
        return lleidahacker

    def activate_lleidahacker(self, userId: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        lleidahacker = self.get_by_id(userId)
        lleidahacker.active = 1
        self.db.commit()
        self.db.refresh(lleidahacker)
        return lleidahacker

    def deactivate_lleidahacker(self, userId: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        lleidahacker = self.get_by_id(userId)
        lleidahacker.active = 0
        self.db.commit()
        self.db.refresh(lleidahacker)
        return lleidahacker
