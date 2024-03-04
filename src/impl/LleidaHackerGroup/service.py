from pydantic import parse_obj_as
from src.impl.LleidaHacker.service import LleidaHackerService
from src.impl.LleidaHackerGroup.model import LleidaHackerGroup as ModelLleidaHackerGroup
from src.utils.UserType import UserType

from src.impl.LleidaHackerGroup.schema import LleidaHackerGroupCreate as LleidaHackerGroupCreateSchema
from src.impl.LleidaHackerGroup.schema import LleidaHackerGroupUpdate as LleidaHackerGroupUpdateSchema
from src.impl.LleidaHackerGroup.schema import LleidaHackerGroupGet as LleidaHackerGroupGetSchema
from src.impl.LleidaHackerGroup.schema import LleidaHackerGroupGetAll as LleidaHackerGroupGetAllSchema
from src.utils.Base.BaseService import BaseService

from src.utils.service_utils import set_existing_data
from src.utils.Token import BaseToken

from src.error.AuthenticationException import AuthenticationException
from src.error.NotFoundException import NotFoundException
from src.error.InvalidDataException import InvalidDataException


class LleidaHackerGroupService(BaseService):
    def __call__(self):
        if self.lleidaHackerService is None:
            self.lleidaHackerService = LleidaHackerService()

    def get_all(self):
        return self.db.query(ModelLleidaHackerGroup).all()
    
    def get_by_id(self, id:int):
        group = self.db.query(ModelLleidaHackerGroup).filter(
            ModelLleidaHackerGroup.id == id).first()
        if group is None:
            raise NotFoundException("LleidaHacker group not found")
        return group

    def get_lleidahackergroup(self, groupId: int, data: BaseToken):
        group = self.get_by_id(groupId)
        users_ids = [u.id for u in group.members]
        if data.check([UserType.LLEIDAHACKER]) and data.user_id in users_ids:
            return parse_obj_as(LleidaHackerGroupGetAllSchema, group)
        return parse_obj_as(LleidaHackerGroupGetSchema, group)

    def add_lleidahackergroup(self, payload: LleidaHackerGroupCreateSchema,
                              data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        hacker = self.lleidaHackerService.get_by_id(data.user_id)
        new_lleidahacker_group = ModelLleidaHackerGroup(**payload.dict(),
                                                        leader_id=hacker.id)
        self.db.add(new_lleidahacker_group)
        self.db.commit()
        self.db.refresh(new_lleidahacker_group)
        return new_lleidahacker_group

    def update_lleidahackergroup(self, groupId: int,
                                 payload: LleidaHackerGroupUpdateSchema,
                                 data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        lleidahacker_group = self.get_by_id(groupId)
        if not data.check([UserType.LLEIDAHACKER], lleidahacker_group.leader_id):
            raise AuthenticationException("Not authorized")
        updated = set_existing_data(lleidahacker_group, payload)
        self.db.commit()
        self.db.refresh(lleidahacker_group)
        return lleidahacker_group, updated

    def delete_lleidahackergroup(self, groupId: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        lleidahacker_group = self.get_by_id(groupId)
        if not data.check([UserType.LLEIDAHACKER], lleidahacker_group.leader_id):
            raise AuthenticationException("Not authorized")
        self.db.delete(lleidahacker_group)
        self.db.commit()
        return lleidahacker_group

    def add_lleidahacker_to_group(self, groupId: int, lleidahackerId: int,
                                  data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        lleidahacker_group = self.get_by_id(groupId)
        lleidahacker = self.lleidaHackerService(lleidahackerId)
        if not data.check([UserType.LLEIDAHACKER], lleidahacker_group.leader_id):
            raise AuthenticationException("Not authorized")
        if lleidahacker is None:
            raise NotFoundException("LleidaHacker not found")
        lleidahacker_group.members.append(lleidahacker)
        self.db.commit()
        self.db.refresh(lleidahacker_group)
        return lleidahacker_group

    def remove_lleidahacker_from_group(self, groupId: int, lleidahackerId: int,
                                       data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        lleidahacker_group = self.get_by_id(groupId)
        if not data.check([UserType.LLEIDAHACKER], lleidahacker_group.leader_id):
            raise AuthenticationException("Not authorized")
        lleidahacker = self.lleidaHackerService(lleidahackerId)
        if lleidahacker not in lleidahacker_group.members:
            raise InvalidDataException("LleidaHacker not in group")
        lleidahacker_group.members.remove(lleidahacker)
        self.db.commit()
        self.db.refresh(lleidahacker_group)
        return lleidahacker_group

    def set_lleidahacker_group_leader(self, groupId: int, lleidahackerId: int,
                                      data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        lleidahacker_group = self.get_by_id(groupId)
        if not data.check([UserType.LLEIDAHACKER], lleidahacker_group.leader_id):
            raise AuthenticationException("Not authorized")
        lleidahacker = self.get_by_id(lleidahackerId)
        if lleidahacker not in lleidahacker_group.members:
            raise InvalidDataException("LleidaHacker not in group")
        lleidahacker_group.leader_id = lleidahacker.id
        lleidahacker_group.leader = lleidahacker

        self.db.commit()
        self.db.refresh(lleidahacker_group)
        return lleidahacker_group
