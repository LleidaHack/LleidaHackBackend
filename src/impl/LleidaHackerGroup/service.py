from fastapi_sqlalchemy import db

from src.error.AuthenticationException import AuthenticationException
from src.error.InvalidDataException import InvalidDataException
from src.error.NotFoundException import NotFoundException
from src.impl.LleidaHacker.service import LleidaHackerService
from src.impl.LleidaHackerGroup.model import LleidaHackerGroup
from src.impl.LleidaHackerGroup.schema import LleidaHackerGroupCreate
from src.impl.LleidaHackerGroup.schema import LleidaHackerGroupGet
from src.impl.LleidaHackerGroup.schema import LleidaHackerGroupGetAll
from src.impl.LleidaHackerGroup.schema import LleidaHackerGroupUpdate
from src.utils.Base.BaseService import BaseService
from src.utils.service_utils import set_existing_data
from src.utils.Token import BaseToken
from src.utils.UserType import UserType


class LleidaHackerGroupService(BaseService):
    name = 'lleidahackergroup_service'
    lleidahacker_service = None

    def get_all(self):
        return db.session.query(LleidaHackerGroup).all()

    def get_by_id(self, id: int):
        group = db.session.query(LleidaHackerGroup).filter(
            LleidaHackerGroup.id == id).first()
        if group is None:
            raise NotFoundException("LleidaHacker group not found")
        return group

    def get_lleidahackergroup(self, groupId: int, data: BaseToken):
        group = self.get_by_id(groupId)
        users_ids = [u.id for u in group.members]
        if data.check([UserType.LLEIDAHACKER]) and data.user_id in users_ids:
            return LleidaHackerGroupGetAll.model_validate(group)
        return LleidaHackerGroupGet.model_validate(group)

    @BaseService.needs_service(LleidaHackerService)
    def add_lleidahackergroup(self, payload: LleidaHackerGroupCreate,
                              data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        hacker = self.lleidahacker_service.get_by_id(data.user_id)
        new_lleidahacker_group = LleidaHackerGroup(**payload.model_dump(),
                                                   leader_id=hacker.id)
        new_lleidahacker_group.members.append(hacker)
        db.session.add(new_lleidahacker_group)
        db.session.commit()
        db.session.refresh(new_lleidahacker_group)
        return new_lleidahacker_group

    def update_lleidahackergroup(self, groupId: int,
                                 payload: LleidaHackerGroupUpdate,
                                 data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        lleidahacker_group = self.get_by_id(groupId)
        if not data.check([UserType.LLEIDAHACKER],
                          lleidahacker_group.leader_id):
            raise AuthenticationException("Not authorized")
        updated = set_existing_data(lleidahacker_group, payload)
        db.session.commit()
        db.session.refresh(lleidahacker_group)
        return lleidahacker_group, updated

    def delete_lleidahackergroup(self, groupId: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        lleidahacker_group = self.get_by_id(groupId)
        if not data.check([UserType.LLEIDAHACKER],
                          lleidahacker_group.leader_id):
            raise AuthenticationException("Not authorized")
        db.session.delete(lleidahacker_group)
        db.session.commit()
        return lleidahacker_group

    @BaseService.needs_service(LleidaHackerService)
    def add_lleidahacker_to_group(self, groupId: int, lleidahackerId: int,
                                  data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        lleidahacker_group = self.get_by_id(groupId)
        lleidahacker = self.lleidahacker_service(lleidahackerId)
        if not data.check([UserType.LLEIDAHACKER],
                          lleidahacker_group.leader_id):
            raise AuthenticationException("Not authorized")
        if lleidahacker is None:
            raise NotFoundException("LleidaHacker not found")
        lleidahacker_group.members.append(lleidahacker)
        db.session.commit()
        db.session.refresh(lleidahacker_group)
        return lleidahacker_group

    @BaseService.needs_service(LleidaHackerService)
    def remove_lleidahacker_from_group(self, groupId: int, lleidahackerId: int,
                                       data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        lleidahacker_group = self.get_by_id(groupId)
        if not data.check([UserType.LLEIDAHACKER],
                          lleidahacker_group.leader_id):
            raise AuthenticationException("Not authorized")
        lleidahacker = self.lleidahacker_service(lleidahackerId)
        if lleidahacker not in lleidahacker_group.members:
            raise InvalidDataException("LleidaHacker not in group")
        lleidahacker_group.members.remove(lleidahacker)
        db.session.commit()
        db.session.refresh(lleidahacker_group)
        return lleidahacker_group

    def set_lleidahacker_group_leader(self, groupId: int, lleidahackerId: int,
                                      data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        lleidahacker_group = self.get_by_id(groupId)
        if not data.check([UserType.LLEIDAHACKER],
                          lleidahacker_group.leader_id):
            raise AuthenticationException("Not authorized")
        lleidahacker = self.get_by_id(lleidahackerId)
        if lleidahacker not in lleidahacker_group.members:
            raise InvalidDataException("LleidaHacker not in group")
        lleidahacker_group.leader_id = lleidahacker.id
        lleidahacker_group.leader = lleidahacker

        db.session.commit()
        db.session.refresh(lleidahacker_group)
        return lleidahacker_group
