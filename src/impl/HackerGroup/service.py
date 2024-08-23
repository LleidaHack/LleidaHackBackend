from typing import List

from fastapi_sqlalchemy import db

from src.error.AuthenticationException import AuthenticationException
from src.error.InvalidDataException import InvalidDataException
from src.error.NotFoundException import NotFoundException
from src.impl.Event.service import EventService
from src.impl.Hacker.service import HackerService
from src.impl.HackerGroup.model import HackerGroup
from src.impl.HackerGroup.model import HackerGroupUser
from src.impl.HackerGroup.schema import HackerGroupCreate
from src.impl.HackerGroup.schema import HackerGroupGet
from src.impl.HackerGroup.schema import HackerGroupGetAll
from src.impl.HackerGroup.schema import HackerGroupUpdate
from src.utils.Base.BaseService import BaseService
from src.utils.service_utils import generate_random_code, set_existing_data
from src.utils.Token import BaseToken
from src.utils.UserType import UserType


class HackerGroupService(BaseService):
    name = 'hackergroup_service'
    event_service: EventService = None
    hacker_service: HackerService = None

    def get_all(self):
        return db.session.query(HackerGroup).all()

    def get_by_id(self, id: int):
        group = db.session.query(HackerGroup).filter(
            HackerGroup.id == id).first()
        if group is None:
            raise NotFoundException("Hacker group not found")
        return group

    def get_when_id_in(self, ids: List[int]):
        return db.session.query(HackerGroup).filter(
            HackerGroup.id.in_(ids)).all()

    def get_by_code(self, code: str, exc=True):
        group = db.session.query(HackerGroup).filter(
            HackerGroup.code == code).first()
        if exc:
            if group is None:
                raise NotFoundException("Hacker group not found")
        return group

    def generate_group_code(self):
        code = ''
        while True:
            code = generate_random_code(10)
            code_exists = self.get_by_code(code, False)
            if code_exists is None:
                break
        return code

    def get_hacker_group(self, id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER, UserType.HACKER]):
            raise AuthenticationException("Not authorized")
        group = self.get_by_id(id)
        members_ids = [h.id for h in group.members]
        if data.check([UserType.HACKER, UserType.LLEIDAHACKER
                       ]) and (data.is_admin or data.user_id in members_ids):
            return HackerGroupGetAll.model_validate(group)
        return HackerGroupGet.model_validate(group)

    @BaseService.needs_service(EventService)
    @BaseService.needs_service(HackerService)
    def add_hacker_group(self, payload: HackerGroupCreate,
                         data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER, UserType.HACKER]):
            raise AuthenticationException("Not authorized")
        members = []
        # event = self.event_service.get_by_id(payload.event_id)
        if not self.event_service.is_registered(payload.event_id,
                                                payload.leader_id, data):
            raise InvalidDataException('Hacker Not registered to event')
        if data.user_type == UserType.HACKER.value:
            hacker = self.hacker_service.get_by_id(data.user_id)
            members.append(hacker)
        # generate a random 10 letter code
        code = self.generate_group_code()
        new_hacker_group = HackerGroup(**payload.model_dump(),
                                            code=code,
                                            members=members)
        db.session.add(new_hacker_group)
        db.session.commit()
        db.session.refresh(new_hacker_group)
        return new_hacker_group

    def update_hacker_group(self, id: int, payload: HackerGroupUpdate,
                            data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER, UserType.HACKER]):
            raise AuthenticationException("Not authorized")
        hacker_group = self.get_by_id(id)
        if not data.check([UserType.HACKER], hacker_group.leader_id):
            raise AuthenticationException("Not authorized")
        updated = set_existing_data(hacker_group, payload)
        db.session.commit()
        return hacker_group, updated

    def delete_hacker_group(self, id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER, UserType.HACKER]):
            raise AuthenticationException("Not authorized")
        hacker_group = self.get_by_id(id)
        if not data.check([UserType.HACKER], hacker_group.leader_id):
            raise AuthenticationException("Not authorized")
        db.session.query(HackerGroupUser).filter(
            HackerGroupUser.group_id == id).delete()
        db.session.delete(hacker_group)
        db.session.commit()
        return hacker_group

    def _add_hacker_to_group(self, group, hacker, event):
        if group.members is None:
            group.members = []
        if hacker.id == group.leader_id:
            raise InvalidDataException('You are the leader of this group')
        if hacker in group.members:
            raise InvalidDataException('You are already on this group')
        if hacker not in event.registered_hackers:
            raise InvalidDataException("Hacker not registered")
        hacker_group_user = db.session.query(HackerGroupUser).filter(
            HackerGroupUser.hacker_id == hacker.id).first()
        if hacker_group_user is not None:
            raise InvalidDataException("Hacker already in a group")
        if len(group.members) >= event.max_group_size:
            raise InvalidDataException("Group is full")
        if hacker in group.members:
            raise InvalidDataException("Hacker already in group")
        group.members.append(hacker)
        db.session.commit()
        db.session.refresh(group)

    @BaseService.needs_service(HackerService)
    @BaseService.needs_service(EventService)
    def add_hacker_to_group(self, groupId: int, hackerId: int,
                            data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER, UserType.HACKER]):
            raise AuthenticationException("Not authorized")
        group = self.get_by_id(groupId)
        hacker = self.hacker_service.get_by_id(hackerId)
        event = self.event_service.get_by_id(group.event_id)
        self._add_hacker_to_group(group, hacker, event)
        return group

    @BaseService.needs_service(EventService)
    @BaseService.needs_service(HackerService)
    def add_hacker_to_group_by_code(self, code: str, hackerId: int,
                                    data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]) or not data.check(
            [UserType.HACKER], hackerId):
            raise AuthenticationException("Not authorized")
        group = self.get_by_code(code)
        hacker = self.hacker_service.get_by_id(hackerId)

        event = self.event_service.get_by_id(group.event_id)
        self._add_hacker_to_group(group, hacker, event)
        return group

    def remove_hacker_from_group(self, groupId: int, hackerId: int,
                                 data: BaseToken):
        deleted = False
        if not data.check([UserType.LLEIDAHACKER, UserType.HACKER.value]):
            raise AuthenticationException("Not authorized")
        hacker_group = self.get_by_id(groupId)
        if not data.check([
                UserType.LLEIDAHACKER.value, UserType.HACKER
        ]) and not data.check(
            [UserType.HACKER], hackerId
        ) and data.user_id != hacker_group.leader_id and data.user_id == hacker_group.leader_id:
            raise InvalidDataException(
                "Cannot remove user from group other than you")
        hacker = [h for h in hacker_group.members if h.id == hackerId]
        hacker_group.members.remove(hacker[0])
        if len(hacker_group.members) == 0:
            db.session.elete(hacker_group)
            deleted = True
        elif hacker_group.leader_id == hackerId:
            hacker_group.leader_id = hacker_group.members[0].id
        db.session.commit()
        if not deleted:
            db.session.refresh(hacker_group)
        return hacker_group

    @BaseService.needs_service(HackerService)
    def set_hacker_group_leader(self, groupId: int, hackerId: int,
                                data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER, UserType.HACKER]):
            raise AuthenticationException("Not authorized")
        hacker_group = self.get_by_id(groupId)
        hacker = self.hacker_service.get_by_id(hackerId)
        if hacker_group.leader_id == hacker.id:
            raise InvalidDataException("Cannot set leader to current leader")
        group_members_ids = [member.id for member in hacker_group.members]
        if not data.check([UserType.LLEIDAHACKER, UserType.HACKER
                           ]) and data.user_id not in group_members_ids:
            raise AuthenticationException("hacker not in group")
        hacker_group.leader_id = hacker.id
        db.session.commit()
        db.session.refresh(hacker_group)
        return hacker_group
