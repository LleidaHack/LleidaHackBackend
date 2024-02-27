from pydantic import parse_obj_as
from sqlalchemy.orm import Session

from src.utils.UserType import UserType
from src.utils.Base.BaseService import BaseService

from src.utils.service_utils import generate_random_code, set_existing_data
from src.utils.Token import BaseToken


from src.impl.HackerGroup.model import HackerGroup as ModelHackerGroup
from src.impl.HackerGroup.model import HackerGroupUser as ModelHackerGroupUser
from src.impl.Hacker.model import Hacker as ModelHacker
from src.impl.Event.model import Event as ModelEvent

from src.impl.HackerGroup.schema import HackerGroupCreate as HackerGroupCreateSchema
from src.impl.HackerGroup.schema import HackerGroupUpdate as HackerGroupUpdateSchema
from src.impl.HackerGroup.schema import HackerGroupGet as HackerGroupGetSchema
from src.impl.HackerGroup.schema import HackerGroupGetAll as HackerGroupGetAllSchema

from src.error.AuthenticationException import AuthenticationException
from src.error.NotFoundException import NotFoundException
from src.error.InvalidDataException import InvalidDataException


class HackerGroupService(BaseService):

    def get_all(self):
        return self.dbquery(ModelHackerGroup).all()

    def get_group_by_code(self, code: str):
        group = self.dbquery(ModelHackerGroup).filter(
            ModelHackerGroup.code == code).first()
        if group is None:
            raise NotFoundException("Hacker group not found")
        return group

    def get_hacker_group(self, id: int, data: BaseToken):
        if not data.is_admin:
            if not (data.available and
                    (data.type == UserType.LLEIDAHACKER.value
                     or data.type == UserType.HACKER.value)):
                raise AuthenticationException("Not authorized")
        group = self.dbquery(ModelHackerGroup).filter(
            ModelHackerGroup.id == id).first()
        if group is None:
            raise NotFoundException("Hacker group not found")
        members_ids = [h.id for h in group.members]
        if data.is_admin or (data.type == UserType.HACKER.value
                             and data.user_id in members_ids
                             ) or data.type == UserType.LLEIDAHACKER.value:
            return parse_obj_as(HackerGroupGetAllSchema, group)
        return parse_obj_as(HackerGroupGetSchema, group)

    def add_hacker_group(self, payload: HackerGroupCreateSchema,
                         data: BaseToken):
        if not data.is_admin:
            if not (data.available and
                    (data.type == UserType.LLEIDAHACKER.value
                     or data.type == UserType.HACKER.value)):
                raise AuthenticationException("Not authorized")
        members = []
        event_exists = self.dbquery(ModelEvent).filter(
            ModelEvent.id == payload.event_id).first()
        if event_exists is None:
            raise NotFoundException("Event not found")
        if data.type == UserType.HACKER.value:
            hacker = self.dbquery(ModelHacker).filter(
                ModelHacker.id == data.user_id).first()
            if hacker is None:
                raise NotFoundException("Hacker not found")
            members.append(hacker)
        # generate a random 10 letter code
        code = ''
        while True:
            code = generate_random_code(10)
            code_exists = self.dbquery(ModelHackerGroup).filter(
                ModelHackerGroup.code == code).first()
            if code_exists is None:
                break
        new_hacker_group = ModelHackerGroup(**payload.dict(),
                                            code=code,
                                            members=members)
        self.dbadd(new_hacker_group)
        self.dbcommit()
        self.dbrefresh(new_hacker_group)
        return new_hacker_group

    def update_hacker_group(self, id: int, payload: HackerGroupUpdateSchema,
                            data: BaseToken):
        if not data.is_admin:
            if not (data.available and
                    (data.type == UserType.LLEIDAHACKER.value
                     or data.type == UserType.HACKER.value)):
                raise AuthenticationException("Not authorized")
        event_exists = self.dbquery(ModelEvent).filter(
            ModelEvent.id == payload.event_id).first()
        if event_exists is None:
            raise NotFoundException("Event not found")
        hacker_group = self.dbquery(ModelHackerGroup).filter(
            ModelHackerGroup.id == id).first()
        if hacker_group is None:
            raise NotFoundException("Hacker group not found")
        if not (data.type == UserType.HACKER.value
                and data.user_id == hacker_group.leader_id):
            raise AuthenticationException("Not authorized")
        updated = set_existing_data(hacker_group, payload)
        self.dbcommit()
        return hacker_group, updated

    def delete_hacker_group(self, id: int, data: BaseToken):
        if not data.is_admin:
            if not (data.available and
                    (data.type == UserType.LLEIDAHACKER.value
                     or data.type == UserType.HACKER.value)):
                raise AuthenticationException("Not authorized")
        hacker_group = self.dbquery(ModelHackerGroup).filter(
            ModelHackerGroup.id == id).first()
        if hacker_group is None:
            raise NotFoundException("Hacker group not found")
        if not (data.type == UserType.HACKER.value
                and data.user_id == hacker_group.leader_id):
            raise AuthenticationException("Not authorized")
        self.dbquery(ModelHackerGroupUser).filter(
            ModelHackerGroupUser.group_id == id).delete()
        self.dbdelete(hacker_group)
        self.dbcommit()
        return hacker_group

    def add_hacker_to_group(self, groupId: int, hackerId: int,
                            data: BaseToken):
        if not data.is_admin:
            if not (data.available and
                    (data.type == UserType.LLEIDAHACKER.value
                     or data.type == UserType.HACKER.value)):
                raise AuthenticationException("Not authorized")
        hacker_group = self.dbquery(ModelHackerGroup).filter(
            ModelHackerGroup.id == groupId).first()
        if hacker_group is None:
            raise NotFoundException("Hacker group not found")
        hacker = self.dbquery(ModelHacker).filter(
            ModelHacker.id == hackerId).first()
        if hacker is None:
            raise NotFoundException("Hacker not found")
        # if hacker_group.members is None:
        #     hacker_group.members = []
        event = self.dbquery(ModelEvent).filter(
            ModelEvent.id == hacker_group.event_id).first()
        if hacker not in event.registered_hackers:
            raise InvalidDataException("Hacker not registered")
        hacker_group_user = self.dbquery(ModelHackerGroupUser).filter(
            ModelHackerGroupUser.hacker_id == hackerId).first()
        if hacker_group_user is not None:
            raise InvalidDataException("Hacker already in group")
        if len(hacker_group.members) >= event.max_group_size:
            raise InvalidDataException("Group is full")
        if hacker in hacker_group.members:
            raise InvalidDataException("Hacker already in group")
        hacker_group.members.append(hacker)
        self.dbcommit()
        self.dbrefresh(hacker_group)
        return hacker_group

    def add_hacker_to_group_by_code(self, code: str, hackerId: int,
                                    data: BaseToken):
        if not data.is_admin:
            if not (data.available and
                    (data.type == UserType.LLEIDAHACKER.value or
                     (data.type == UserType.HACKER.value
                      and data.user_id == hackerId))):
                raise AuthenticationException("Not authorized")
        hacker_group = self.dbquery(ModelHackerGroup).filter(
            ModelHackerGroup.code == code).first()
        if hacker_group is None:
            raise NotFoundException("Hacker group not found")
        hacker = self.dbquery(ModelHacker).filter(
            ModelHacker.id == hackerId).first()
        if hacker is None:
            raise NotFoundException("Hacker not found")
        if hacker_group.members is None:
            hacker_group.members = []
        event = self.dbquery(ModelEvent).filter(
            ModelEvent.id == hacker_group.event_id).first()
        if hacker not in event.registered_hackers:
            raise InvalidDataException("Hacker not registered")
        hacker_group_user = self.dbquery(ModelHackerGroupUser).filter(
            ModelHackerGroupUser.hacker_id == hackerId).first()
        if hacker_group_user is not None:
            raise InvalidDataException("Hacker already in group")
        if len(hacker_group.members) >= event.max_group_size:
            raise InvalidDataException("Group is full")
        if hacker in hacker_group.members:
            raise InvalidDataException("Hacker already in group")
        hacker_group.members.append(hacker)
        self.dbcommit()
        self.dbrefresh(hacker_group)
        return hacker_group

    def remove_hacker_from_group(self, groupId: int, hackerId: int,
                                 data: BaseToken):
        deleted = False
        if not data.is_admin:
            if not (data.available and
                    (data.type == UserType.LLEIDAHACKER.value
                     or data.type == UserType.HACKER.value)):
                raise AuthenticationException("Not authorized")
        hacker_group = self.dbquery(ModelHackerGroup).filter(
            ModelHackerGroup.id == groupId).first()
        if hacker_group is None:
            raise NotFoundException("Hacker group not found")
        if not data.is_admin:
            if not (data.type == UserType.LLEIDAHACKER.value or
                    (data.type == UserType.HACKER.value and
                     (data.user_id == hackerId
                      and data.user_id != hacker_group.leader_id) or
                     (data.user_id == hacker_group.leader_id))):
                raise InvalidDataException(
                    "Cannot remove user from group other than you")
        hacker = [h for h in hacker_group.members if h.id == hackerId]
        hacker_group.members.remove(hacker[0])
        if len(hacker_group.members) == 0:
            self.dbdelete(hacker_group)
            deleted = True
        elif hacker_group.leader_id == hackerId:
            hacker_group.leader_id = hacker_group.members[0].id
        self.dbcommit()
        if not deleted:
            self.dbrefresh(hacker_group)
        return hacker_group

    def set_hacker_group_leader(self, groupId: int, hackerId: int,
                                data: BaseToken):
        if not data.is_admin:
            if not (data.available and
                    (data.type == UserType.LLEIDAHACKER.value
                     or data.type == UserType.HACKER.value)):
                raise AuthenticationException("Not authorized")
        hacker_group = self.db.query(ModelHackerGroup).filter(
            ModelHackerGroup.id == groupId).first()
        if hacker_group is None:
            raise NotFoundException("Hacker group not found")
        hacker = self.db.query(ModelHacker).filter(
            ModelHacker.id == hackerId).first()
        if hacker is None:
            raise NotFoundException("Hacker not found")
        if hacker_group.leader_id == hacker.id:
            raise InvalidDataException("Cannot set leader to current leader")
        group_members_ids = [member.id for member in hacker_group.members]
        if not data.is_admin:
            if not (data.type == UserType.LLEIDAHACKER or
                    (data.type == UserType.HACKER.value
                     and data.user_id in group_members_ids)):
                raise AuthenticationException("hacker not in group")
        hacker_group.leader_id = hacker.id
        self.dbcommit()
        self.dbrefresh(hacker_group)
        return hacker_group
