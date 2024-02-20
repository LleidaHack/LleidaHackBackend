from datetime import datetime as date
from pydantic import parse_obj_as

from security import get_password_hash
from src.utils import TokenData
from src.utils.UserType import UserType
from utils.BaseService import BaseService

from utils.service_utils import set_existing_data, check_image, generate_user_code
from utils.service_utils import check_user

from src.error.AuthenticationException import AuthenticationException
from src.error.NotFoundException import NotFoundException

from src.impl.LleidaHacker.model import LleidaHacker as ModelLleidaHacker

from src.impl.LleidaHacker.schema import LleidaHackerCreate as LleidaHackerCreateSchema
from src.impl.LleidaHacker.schema import LleidaHackerUpdate as LleidaHackerUpdateSchema
from src.impl.LleidaHacker.schema import LleidaHackerGet as LleidaHackerGetSchema
from src.impl.LleidaHacker.schema import LleidaHackerGetAll as LleidaHackerGetAllSchema

class LleidaHackerService(BaseService):
    def get_all(self):
        return self.db.query(ModelLleidaHacker).all()


    def get_lleidahacker(self, userId: int, data: TokenData):
        user = self.db.query(ModelLleidaHacker).filter(
            ModelLleidaHacker.id == userId).first()
        if user is None:
            raise NotFoundException("LleidaHacker not found")
        if data.is_admin or (data.available and
                            (data.type == UserType.LLEIDAHACKER.value
                            and data.user_id == userId)):
            return parse_obj_as(LleidaHackerGetAllSchema, user)
        return parse_obj_as(LleidaHackerGetSchema, user)


    def add_lleidahacker(self, payload: LleidaHackerCreateSchema):
        check_user(db, payload.email, payload.nickname, payload.telephone)
        if payload.image is not None:
            payload = check_image(payload)
        new_lleidahacker = ModelLleidaHacker(**payload.dict(),
                                            code=generate_user_code(self.db))
        new_lleidahacker.password = get_password_hash(payload.password)
        self.db.add(new_lleidahacker)
        self.db.commit()
        self.db.refresh(new_lleidahacker)
        return new_lleidahacker


    def update_lleidahacker(self, userId: int, payload: LleidaHackerUpdateSchema,
                            data: TokenData):
        if not data.is_admin:
            if not (data.available and (data.type == UserType.LLEIDAHACKER.value
                                        and data.user_id == userId)):
                raise AuthenticationException("Not authorized")
        lleidahacker = self.db.query(ModelLleidaHacker).filter(
            ModelLleidaHacker.id == userId).first()
        if lleidahacker is None:
            raise NotFoundException("LleidaHacker not found")
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


    def delete_lleidahacker(self, userId: int, data: TokenData):
        if not data.is_admin:
            if not (data.available and (data.type == UserType.LLEIDAHACKER.value
                                        and data.user_id == userId)):
                raise AuthenticationException("Not authorized")
        lleidahacker = self.db.query(ModelLleidaHacker).filter(
            ModelLleidaHacker.id == userId).first()
        if lleidahacker is None:
            raise NotFoundException("LleidaHacker not found")
        self.db.delete(lleidahacker)
        self.db.commit()
        return lleidahacker


    def accept_lleidahacker(self, userId: int, data: TokenData):
        if not data.is_admin:
            if not (data.available and data.type == UserType.LLEIDAHACKER.value):
                raise AuthenticationException("Not authorized")
        lleidahacker = self.db.query(ModelLleidaHacker).filter(
            ModelLleidaHacker.id == userId).first()
        if lleidahacker is None:
            raise NotFoundException("LleidaHacker not found")
        lleidahacker.active = 1
        lleidahacker.accepted = 1
        lleidahacker.rejected = 0
        self.db.commit()
        self.db.refresh(lleidahacker)
        return lleidahacker


    def reject_lleidahacker(self, userId: int, data: TokenData):
        if not data.is_admin:
            if not (data.available and data.type == UserType.LLEIDAHACKER.value):
                raise AuthenticationException("Not authorized")
        lleidahacker = self.db.query(ModelLleidaHacker).filter(
            ModelLleidaHacker.id == userId).first()
        if lleidahacker is None:
            raise NotFoundException("LleidaHacker not found")
        lleidahacker.active = 0
        lleidahacker.accepted = 0
        lleidahacker.rejected = 1
        self.db.commit()
        self.db.refresh(lleidahacker)
        return lleidahacker


    def activate_lleidahacker(self, userId: int, data: TokenData):
        if not data.is_admin:
            if not (data.available and data.type == UserType.LLEIDAHACKER.value):
                raise AuthenticationException("Not authorized")
        lleidahacker = self.db.query(ModelLleidaHacker).filter(
            ModelLleidaHacker.id == userId).first()
        if lleidahacker is None:
            raise NotFoundException("LleidaHacker not found")
        lleidahacker.active = 1
        self.db.commit()
        self.db.refresh(lleidahacker)
        return lleidahacker


    def deactivate_lleidahacker(self, userId: int, data: TokenData):
        if not data.is_admin:
            if not (data.available and data.type == UserType.LLEIDAHACKER.value):
                raise AuthenticationException("Not authorized")
        lleidahacker = self.db.query(ModelLleidaHacker).filter(
            ModelLleidaHacker.id == userId).first()
        if lleidahacker is None:
            raise NotFoundException("LleidaHacker not found")
        lleidahacker.active = 0
        self.db.commit()
        self.db.refresh(lleidahacker)
        return lleidahacker
