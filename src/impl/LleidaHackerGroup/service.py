from fastapi_sqlalchemy import db

from src.error.AuthenticationError import AuthenticationError
from src.error.InvalidDataError import InvalidDataError
from src.error.NotFoundError import NotFoundError
from src.impl.LleidaHacker.service import LleidaHackerService
from src.impl.LleidaHackerGroup.model import (
    LleidaHackerGroup,
    LleidaHackerGroupLeader,
    LleidaHackerGroupUser,
)
from src.impl.LleidaHackerGroup.schema import (
    LleidaHackerGroupCreate,
    LleidaHackerGroupGet,
    LleidaHackerGroupGetAll,
    LleidaHackerGroupUpdate,
)
from src.utils.Base.BaseService import BaseService
from src.utils.service_utils import set_existing_data
from src.utils.token import BaseToken
from src.utils.user_type import UserType


class LleidaHackerGroupService(BaseService):
    name = 'lleidahackergroup_service'
    lleidahacker_service = None

    def get_all(self):
        return db.session.query(LleidaHackerGroup).all()

    def get_by_id(self, item_id: int):
        group = (
            db.session.query(LleidaHackerGroup)
            .filter(LleidaHackerGroup.id == item_id)
            .first()
        )
        if group is None:
            raise NotFoundError('LleidaHacker group not found')
        return group

    def get_lleidahackergroup(self, group_id: int, data: BaseToken):
        group = self.get_by_id(group_id)
        users_ids = [u.id for u in group.members]
        if data.check([UserType.LLEIDAHACKER]) and data.user_id in users_ids:
            return LleidaHackerGroupGetAll.model_validate(group)
        return LleidaHackerGroupGet.model_validate(group)

    @BaseService.needs_service(LleidaHackerService)
    def add_lleidahackergroup(self, payload: LleidaHackerGroupCreate, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationError('Not authorized')
        hacker = self.lleidahacker_service.get_by_id(data.user_id)
        new_lleidahacker_group = LleidaHackerGroup(
            **payload.model_dump(), leader_id=hacker.id
        )
        new_lleidahacker_group.members.append(hacker)
        db.session.add(new_lleidahacker_group)
        db.session.commit()
        db.session.refresh(new_lleidahacker_group)
        return new_lleidahacker_group

    def update_lleidahackergroup(
        self, group_id: int, payload: LleidaHackerGroupUpdate, data: BaseToken
    ):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationError('Not authorized')
        lleidahacker_group = self.get_by_id(group_id)
        if not data.check([UserType.LLEIDAHACKER], lleidahacker_group.leader_id):
            raise AuthenticationError('Not authorized')
        updated = set_existing_data(lleidahacker_group, payload)
        db.session.commit()
        db.session.refresh(lleidahacker_group)
        return lleidahacker_group, updated

    def delete_lleidahackergroup(self, group_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationError('Not authorized')
        lleidahacker_group = self.get_by_id(group_id)
        if not data.check([UserType.LLEIDAHACKER], lleidahacker_group.leader_id):
            raise AuthenticationError('Not authorized')
        db.session.delete(lleidahacker_group)
        db.session.commit()
        return lleidahacker_group

    @BaseService.needs_service(LleidaHackerService)
    def add_lleidahacker_to_group(
        self, group_id: int, lleidahacker_id: int, primary: bool, data: BaseToken
    ):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationError('Not authorized')
        lleidahacker_group = self.get_by_id(group_id)
        lleidahacker = self.lleidahacker_service.get_by_id(lleidahacker_id)
        if not data.check([UserType.LLEIDAHACKER], lleidahacker_group.leader_id):
            raise AuthenticationError('Not authorized')
        if lleidahacker is None:
            raise NotFoundError('LleidaHacker not found')
        grp_usr = LleidaHackerGroupUser(
            group_id=group_id, user_id=lleidahacker_id, primary=primary
        )
        db.session.add(grp_usr)
        db.session.commit()
        db.session.refresh(lleidahacker_group)
        return lleidahacker_group

    @BaseService.needs_service(LleidaHackerService)
    def remove_lleidahacker_from_group(
        self, group_id: int, lleidahacker_id: int, data: BaseToken
    ):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationError('Not authorized')
        lleidahacker_group = self.get_by_id(group_id)
        if not data.check([UserType.LLEIDAHACKER], lleidahacker_group.leader_id):
            raise AuthenticationError('Not authorized')
        lleidahacker = self.lleidahacker_service.get_by_id(lleidahacker_id)
        if lleidahacker not in lleidahacker_group.members:
            raise InvalidDataError('LleidaHacker not in group')
        lleidahacker_group.members.remove(lleidahacker)
        db.session.commit()
        db.session.refresh(lleidahacker_group)
        return lleidahacker_group

    def add_lleidahacker_group_leader(
        self, group_id: int, lleidahacker_id: int, data: BaseToken
    ):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationError('Not authorized')
        lleidahacker_group = self.get_by_id(group_id)
        if not data.check([UserType.LLEIDAHACKER], lleidahacker_group.leader_id):
            raise AuthenticationError('Not authorized')
        lleidahacker = self.lleidahacker_service.get_by_id(lleidahacker_id)
        if lleidahacker not in lleidahacker_group.members:
            raise InvalidDataError('LleidaHacker not in group')
        grp_ldr = LleidaHackerGroupLeader(group_id=group_id, user_id=lleidahacker_id)
        db.session.add(grp_ldr)
        db.session.commit()
        db.session.refresh(lleidahacker_group)
        return lleidahacker_group

    def remove_lleidahacker_group_leader(
        self, group_id: int, lleidahacker_id: int, data: BaseToken
    ):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationError('Not authorized')
        lleidahacker_group = self.get_by_id(group_id)
        if not data.check([UserType.LLEIDAHACKER], lleidahacker_group.leader_id):
            raise AuthenticationError('Not authorized')
        lleidahacker = self.lleidahacker_service.get_by_id(lleidahacker_id)
        if lleidahacker not in lleidahacker_group.members:
            raise InvalidDataError('LleidaHacker not in group')
        grp_ldr = (
            db.session.query(LleidaHackerGroupLeader)
            .filter(
                LleidaHackerGroupLeader.group_id == group_id,
                LleidaHackerGroupLeader.user_id == lleidahacker_id,
            )
            .first()
        )
        if grp_ldr is None:
            raise NotFoundError('LleidaHacker not leader of group')
        db.session.delete(grp_ldr)
        db.session.commit()
        db.session.refresh(lleidahacker_group)
        return lleidahacker_group

    # llhk_groups:[

    # {
    # 	nom: 'devs',
    # 	img: ...,
    # 	caps: [{},]
    # 	members: [
    # 		{id: 12, nom: ton},
    # 	]
    # },
    # ]

    @BaseService.needs_service(LleidaHackerService)
    def get_sorted(self):
        grps = self.get_all()
        user_group_reg = (
            db.session.query(LleidaHackerGroupUser)
            .filter(LleidaHackerGroupUser.primary)
            .all()
        )
        users = {_.id: _ for _ in self.lleidahacker_service.get_all()}
        return {
            'llhk_groups': [
                {
                    'name': _.name,
                    'img': _.image,
                    'leaders': _.leaders,
                    'members': [
                        users[u.user_id] for u in user_group_reg if u.group_id == _.id
                    ],
                }
                for _ in grps
            ]
        }
