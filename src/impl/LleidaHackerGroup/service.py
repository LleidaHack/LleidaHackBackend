from fastapi_sqlalchemy import db

from src.error.AuthorizationException import AuthorizationException
from src.error.InvalidDataException import InvalidDataException
from src.error.NotFoundException import NotFoundException
from src.impl.LleidaHacker.service import LleidaHackerService
from src.impl.LleidaHackerGroup.model import LleidaHackerGroup, LleidaHackerGroupUser
from src.impl.LleidaHackerGroup.schema import (
    LleidaHackerGroupCreate,
    LleidaHackerGroupGet,
    LleidaHackerGroupUpdate,
)
from src.utils.Base.BaseService import BaseService
from src.utils.service_utils import set_existing_data
from src.utils.Token import BaseToken
from src.utils.UserType import UserType


class LleidaHackerGroupService(BaseService):
    name = "lleidahackergroup_service"
    lleidahacker_service = None

    def get_all(self):
        return db.session.query(LleidaHackerGroup).all()

    def get_by_id(self, group_id: int):
        group = db.session.get(LleidaHackerGroup, group_id)
        if group is None:
            raise NotFoundException("LleidaHacker group not found")
        return group

    def get_managed_group(self, group_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthorizationException("Not authorized")
        group = (
            db.session.query(LleidaHackerGroup)
            .filter_by(id=group_id)
            .populate_existing()
            .with_for_update()
            .first()
        )
        if group is None:
            raise NotFoundException("LleidaHacker group not found")
        if not data.is_admin and data.user_id not in {
            leader.id for leader in group.leaders
        }:
            raise AuthorizationException("Only group leaders can manage this group")
        return group

    def get_lleidahackergroup(self, groupId: int, data: BaseToken):
        return LleidaHackerGroupGet.model_validate(self.get_by_id(groupId))

    @BaseService.needs_service(LleidaHackerService)
    def add_lleidahackergroup(self, payload: LleidaHackerGroupCreate, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]) or data.user_id == 0:
            raise AuthorizationException(
                "An organizer account is required to create a group"
            )
        creator = self.lleidahacker_service.get_by_id(data.user_id)
        group = LleidaHackerGroup(
            **payload.model_dump(), members=[creator], leaders=[creator]
        )
        db.session.add(group)
        db.session.commit()
        db.session.refresh(group)
        return group

    def update_lleidahackergroup(
        self, groupId: int, payload: LleidaHackerGroupUpdate, data: BaseToken
    ):
        group = self.get_managed_group(groupId, data)
        updated = set_existing_data(group, payload)
        db.session.commit()
        db.session.refresh(group)
        return group, updated

    def delete_lleidahackergroup(self, groupId: int, data: BaseToken):
        group = self.get_managed_group(groupId, data)
        db.session.delete(group)
        db.session.commit()
        return group

    @BaseService.needs_service(LleidaHackerService)
    def add_lleidahacker_to_group(
        self, groupId: int, lleidahackerId: int, primary: bool, data: BaseToken
    ):
        group = self.get_managed_group(groupId, data)
        member = self.lleidahacker_service.get_by_id(lleidahackerId)
        if member in group.members:
            raise InvalidDataException("LleidaHacker already belongs to this group")
        db.session.add(
            LleidaHackerGroupUser(group_id=groupId, user_id=member.id, primary=primary)
        )
        db.session.commit()
        db.session.refresh(group)
        return group

    @BaseService.needs_service(LleidaHackerService)
    def remove_lleidahacker_from_group(
        self, groupId: int, lleidahackerId: int, data: BaseToken
    ):
        group = self.get_managed_group(groupId, data)
        member = self.lleidahacker_service.get_by_id(lleidahackerId)
        if member not in group.members:
            raise InvalidDataException("LleidaHacker is not a member of this group")
        if member in group.leaders:
            if len(group.leaders) == 1:
                raise InvalidDataException(
                    "Assign another leader before removing the last leader"
                )
            group.leaders.remove(member)
        group.members.remove(member)
        db.session.commit()
        db.session.refresh(group)
        return group

    @BaseService.needs_service(LleidaHackerService)
    def add_lleidahacker_group_leader(
        self, groupId: int, lleidahackerId: int, data: BaseToken
    ):
        group = self.get_managed_group(groupId, data)
        member = self.lleidahacker_service.get_by_id(lleidahackerId)
        if member not in group.members:
            raise InvalidDataException("The leader must be a member of the group")
        if member in group.leaders:
            raise InvalidDataException("LleidaHacker is already a leader")
        group.leaders.append(member)
        db.session.commit()
        db.session.refresh(group)
        return group

    @BaseService.needs_service(LleidaHackerService)
    def remove_lleidahacker_group_leader(
        self, groupId: int, lleidahackerId: int, data: BaseToken
    ):
        group = self.get_managed_group(groupId, data)
        member = self.lleidahacker_service.get_by_id(lleidahackerId)
        if member not in group.leaders:
            raise NotFoundException("LleidaHacker is not a leader of this group")
        if len(group.leaders) == 1:
            raise InvalidDataException("A group must retain at least one leader")
        group.leaders.remove(member)
        db.session.commit()
        db.session.refresh(group)
        return group

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
            "llhk_groups": [
                {
                    "name": _.name,
                    "img": _.image,
                    "leaders": _.leaders,
                    "members": [
                        users[u.user_id] for u in user_group_reg if u.group_id == _.id
                    ],
                }
                for _ in grps
            ]
        }
