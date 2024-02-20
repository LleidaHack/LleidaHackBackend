from pydantic import parse_obj_as
from src.impl.LleidaHacker.model import LleidaHackerGroup as ModelLleidaHackerGroup
from src.impl.LleidaHacker.model import LleidaHacker as ModelLleidaHacker
from src.utils.TokenData import TokenData
from src.utils.UserType import UserType

from src.impl.LleidaHackerGroup.schema import LleidaHackerGroupCreate as LleidaHackerGroupCreateSchema
from src.impl.LleidaHackerGroup.schema import LleidaHackerGroupUpdate as LleidaHackerGroupUpdateSchema
from src.impl.LleidaHackerGroup.schema import LleidaHackerGroupGet as LleidaHackerGroupGetSchema
from src.impl.LleidaHackerGroup.schema import LleidaHackerGroupGetAll as LleidaHackerGroupGetAllSchema
from utils.BaseService import BaseService

from utils.service_utils import set_existing_data

from src.error.AuthenticationException import AuthenticationException
from src.error.NotFoundException import NotFoundException
from src.error.InvalidDataException import InvalidDataException


class LleidaHackerGroupService(BaseService):

    def get_all(self):
        return self.db.query(ModelLleidaHackerGroup).all()

    def get_lleidahackergroup(self, groupId: int, data: TokenData):
        group = self.db.query(ModelLleidaHackerGroup).filter(
            ModelLleidaHackerGroup.id == groupId).first()
        if group is None:
            raise NotFoundException("LleidaHacker group not found")
        users_ids = [u.id for u in group.members]
        if data.is_admin or (data.available
                             and data.type == UserType.LLEIDAHACKER.value
                             and data.user_id in users_ids):
            return parse_obj_as(LleidaHackerGroupGetAllSchema, group)
        return parse_obj_as(LleidaHackerGroupGetSchema, group)

    def add_lleidahackergroup(self, payload: LleidaHackerGroupCreateSchema,
                              data: TokenData):
        if not data.is_admin:
            if not (data.available
                    and data.user_type == UserType.LLEIDAHACKER.value):
                raise AuthenticationException("Not authorized")
        hacker = self.db.query(ModelLleidaHacker).filter(
            ModelLleidaHacker.id == data.user_id).first()
        if hacker is None:
            raise NotFoundException("LleidaHacker not found")
        new_lleidahacker_group = ModelLleidaHackerGroup(**payload.dict(),
                                                        leader_id=hacker.id)
        self.db.add(new_lleidahacker_group)
        self.db.commit()
        self.db.refresh(new_lleidahacker_group)
        return new_lleidahacker_group

    def update_lleidahackergroup(self, groupId: int,
                                 payload: LleidaHackerGroupUpdateSchema,
                                 data: TokenData):
        if not data.is_admin:
            if not (data.available
                    and data.user_type == UserType.LLEIDAHACKER.value):
                raise AuthenticationException("Not authorized")
        lleidahacker_group = self.db.query(ModelLleidaHackerGroup).filter(
            ModelLleidaHackerGroup.id == groupId).first()
        if lleidahacker_group is None:
            raise NotFoundException("LleidaHacker group not found")
        if not (data.user_type == UserType.LLEIDAHACKER.value
                and data.user_id == lleidahacker_group.leader_id):
            raise AuthenticationException("Not authorized")
        updated = set_existing_data(lleidahacker_group, payload)
        self.db.commit()
        self.db.refresh(lleidahacker_group)
        return lleidahacker_group, updated

    def delete_lleidahackergroup(self, groupId: int, data: TokenData):
        if not data.is_admin:
            if not (data.available
                    and data.user_type == UserType.LLEIDAHACKER.value):
                raise AuthenticationException("Not authorized")
        lleidahacker_group = self.db.query(ModelLleidaHackerGroup).filter(
            ModelLleidaHackerGroup.id == groupId).first()
        if lleidahacker_group is None:
            raise NotFoundException("LleidaHacker group not found")
        if not (data.user_type == UserType.LLEIDAHACKER.value
                and data.user_id == lleidahacker_group.leader_id):
            raise AuthenticationException("Not authorized")
        self.db.delete(lleidahacker_group)
        self.db.commit()
        return lleidahacker_group

    def add_lleidahacker_to_group(self, groupId: int, lleidahackerId: int,
                                  data: TokenData):
        if not data.is_admin:
            if not (data.available
                    and data.user_type == UserType.LLEIDAHACKER.value):
                raise AuthenticationException("Not authorized")
        lleidahacker_group = self.db.query(ModelLleidaHackerGroup).filter(
            ModelLleidaHackerGroup.id == groupId).first()
        if lleidahacker_group is None:
            raise NotFoundException("LleidaHacker group not found")
        lleidahacker = self.db.query(ModelLleidaHacker).filter(
            ModelLleidaHacker.id == lleidahackerId).first()
        if not (data.user_type == UserType.LLEIDAHACKER.value
                and data.user_id == lleidahacker_group.leader_id):
            raise AuthenticationException("Not authorized")
        if lleidahacker is None:
            raise NotFoundException("LleidaHacker not found")
        lleidahacker_group.members.append(lleidahacker)
        self.db.commit()
        self.db.refresh(lleidahacker_group)
        return lleidahacker_group

    def remove_lleidahacker_from_group(self, groupId: int, lleidahackerId: int,
                                       data: TokenData):
        if not data.is_admin:
            if not (data.available
                    and data.user_type == UserType.LLEIDAHACKER.value):
                raise AuthenticationException("Not authorized")
        lleidahacker_group = self.db.query(ModelLleidaHackerGroup).filter(
            ModelLleidaHackerGroup.id == groupId).first()
        if lleidahacker_group is None:
            raise NotFoundException("LleidaHacker group not found")
        if not (data.user_type == UserType.LLEIDAHACKER.value
                and data.user_id == lleidahacker_group.leader_id):
            raise AuthenticationException("Not authorized")
        lleidahacker = self.db.query(ModelLleidaHacker).filter(
            ModelLleidaHacker.id == lleidahackerId).first()
        if lleidahacker is None:
            raise NotFoundException("LleidaHacker not found")
        if lleidahacker not in lleidahacker_group.members:
            raise InvalidDataException("LleidaHacker not in group")
        lleidahacker_group.members.remove(lleidahacker)
        self.db.commit()
        self.db.refresh(lleidahacker_group)
        return lleidahacker_group

    def set_lleidahacker_group_leader(self, groupId: int, lleidahackerId: int,
                                      data: TokenData):
        if not data.is_admin:
            if not (data.available
                    and data.user_type == UserType.LLEIDAHACKER.value):
                raise AuthenticationException("Not authorized")
        lleidahacker_group = self.db.query(ModelLleidaHackerGroup).filter(
            ModelLleidaHackerGroup.id == groupId).first()
        if lleidahacker_group is None:
            raise NotFoundException("LleidaHacker group not found")
        if not (data.user_type == UserType.LLEIDAHACKER.value
                and data.user_id == lleidahacker_group.leader_id):
            raise AuthenticationException("Not authorized")
        lleidahacker = self.db.query(ModelLleidaHacker).filter(
            ModelLleidaHacker.id == lleidahackerId).first()
        if lleidahacker is None:
            raise NotFoundException("LleidaHacker not found")
        if lleidahacker not in lleidahacker_group.members:
            raise InvalidDataException("LleidaHacker not in group")
        lleidahacker_group.leader_id = lleidahacker.id
        lleidahacker_group.leader = lleidahacker

        self.db.commit()
        self.db.refresh(lleidahacker_group)
        return lleidahacker_group
