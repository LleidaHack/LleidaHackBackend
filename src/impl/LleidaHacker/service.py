from datetime import datetime as date

from fastapi_sqlalchemy import db

from src.error.AuthenticationError import AuthenticationError
from src.error.NotFoundError import NotFoundError
from src.impl.LleidaHacker.model import LleidaHacker
from src.impl.LleidaHacker.schema import (
    LleidaHackerCreate,
    LleidaHackerGet,
    LleidaHackerGetAll,
    LleidaHackerUpdate,
)
from src.impl.LleidaHackerGroup.model import LleidaHackerGroup, LleidaHackerGroupUser
from src.impl.UserConfig.model import UserConfig
from src.utils.Base.BaseService import BaseService
from src.utils.security import get_password_hash
from src.utils.service_utils import (
    check_image,
    check_user,
    generate_user_code,
    set_existing_data,
)
from src.utils.token import BaseToken
from src.utils.user_type import UserType


class LleidaHackerService(BaseService):
    name = 'lleidahacker_service'

    def get_all(self):
        return db.session.query(LleidaHacker).all()

    def get_by_id(self, item_id: int):
        user = db.session.query(LleidaHacker).filter(LleidaHacker.id == item_id).first()
        if user is None:
            raise NotFoundError('LleidaHacker not found')
        return user

    def get_lleidahacker(self, user_id: int, data: BaseToken):
        user = self.get_by_id(user_id)
        if type(data) is not bool and data.check([UserType.LLEIDAHACKER], user_id):
            return LleidaHackerGetAll.model_validate(user)
        return LleidaHackerGet.model_validate(user)

    def add_lleidahacker(self, payload: LleidaHackerCreate):
        check_user(payload.email, payload.nickname, payload.telephone)
        if payload.image is not None:
            payload = check_image(payload)
        new_lleidahacker = LleidaHacker(
            **payload.model_dump(exclude={'config'}), code=generate_user_code()
        )
        new_lleidahacker.password = get_password_hash(payload.password)
        new_lleidahacker.active = True

        new_config = UserConfig(**payload.config.model_dump())

        db.session.add(new_config)
        db.session.flush()
        new_lleidahacker.config_id = new_config.id
        db.session.add(new_lleidahacker)
        db.session.commit()
        db.session.refresh(new_lleidahacker)
        return new_lleidahacker

    def update_lleidahacker(
        self, user_id: int, payload: LleidaHackerUpdate, data: BaseToken
    ):
        if not data.check([UserType.LLEIDAHACKER], user_id):
            raise AuthenticationError('Not authorized')
        lleidahacker = self.get_by_id(user_id)
        if payload.image is not None:
            payload = check_image(payload)
        updated = set_existing_data(lleidahacker, payload)
        lleidahacker.updated_at = date.now()
        updated.append('updated_at')
        if payload.password is not None:
            lleidahacker.password = get_password_hash(payload.password)
        db.session.commit()
        db.session.refresh(lleidahacker)
        return lleidahacker, updated

    def delete_lleidahacker(self, user_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER], user_id):
            raise AuthenticationError('Not authorized')
        lleidahacker = self.get_by_id(user_id)
        group_users = (
            db.session.query(LleidaHackerGroupUser)
            .filter(LleidaHackerGroupUser.user_id == user_id)
            .all()
        )
        ids = [_.group_id for _ in group_users]
        groups = (
            db.session.query(LleidaHackerGroup)
            .filter(LleidaHackerGroup.id.in_(ids))
            .all()
        )
        for g in groups:
            g.members.remove(lleidahacker)
            if g.leader_id == user_id:
                if len(g.members) > 1:
                    g.leader_id = g.members[0].id
                else:
                    db.session.query(LleidaHackerGroup).filter(
                        LleidaHackerGroup.id == g.id
                    ).delete()
        db.session.delete(lleidahacker)
        db.session.commit()
        return lleidahacker

    def accept_lleidahacker(self, user_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationError('Not authorized')
        lleidahacker = self.get_by_id(user_id)
        lleidahacker.active = 1
        lleidahacker.accepted = 1
        lleidahacker.rejected = 0
        db.session.commit()
        db.session.refresh(lleidahacker)
        return lleidahacker

    def reject_lleidahacker(self, user_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationError('Not authorized')
        lleidahacker = self.get_by_id(user_id)
        lleidahacker.active = 0
        lleidahacker.accepted = 0
        lleidahacker.rejected = 1
        db.session.commit()
        db.session.refresh(lleidahacker)
        return lleidahacker

    def activate_lleidahacker(self, user_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationError('Not authorized')
        lleidahacker = self.get_by_id(user_id)
        lleidahacker.active = 1
        db.session.commit()
        db.session.refresh(lleidahacker)
        return lleidahacker

    def deactivate_lleidahacker(self, user_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationError('Not authorized')
        lleidahacker = self.get_by_id(user_id)
        lleidahacker.active = 0
        db.session.commit()
        db.session.refresh(lleidahacker)
        return lleidahacker
