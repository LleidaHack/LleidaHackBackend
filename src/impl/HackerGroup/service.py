from typing import List

from fastapi_sqlalchemy import db

from src.error.AuthorizationException import AuthorizationException
from src.error.InvalidDataException import InvalidDataException
from src.error.NotFoundException import NotFoundException
from src.impl.Event.service import EventService
from src.impl.Hacker.service import HackerService
from src.impl.Hacker.model import Hacker
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
    name = "hackergroup_service"
    event_service: EventService = None
    hacker_service: HackerService = None

    def get_all(self):
        return db.session.query(HackerGroup).all()

    def get_by_id(self, id: int):
        group = db.session.query(HackerGroup).filter(HackerGroup.id == id).first()
        if group is None:
            raise NotFoundException("Hacker group not found")
        return group

    def get_for_update(self, group_id: int):
        group = (db.session.query(HackerGroup).filter_by(id=group_id)
                 .populate_existing().with_for_update().first())
        if group is None:
            raise NotFoundException("Hacker group not found")
        return group

    @staticmethod
    def can_manage(group, data):
        return data.check([UserType.LLEIDAHACKER]) or data.check([UserType.HACKER], group.leader_id)

    @staticmethod
    def validate_leader(group, leader_id):
        if leader_id not in {member.id for member in group.members}:
            raise InvalidDataException("The leader must be a member of the group")

    def lock_hacker(self, hacker_id):
        hacker = (db.session.query(Hacker).filter(Hacker.id == hacker_id)
                  .with_for_update().first())
        if hacker is None:
            raise NotFoundException("Hacker not found")
        return hacker

    def get_when_id_in(self, ids: List[int]):
        return db.session.query(HackerGroup).filter(HackerGroup.id.in_(ids)).all()

    def get_by_code(self, code: str, exc=True):
        group = db.session.query(HackerGroup).filter(HackerGroup.code == code).first()
        if exc:
            if group is None:
                raise NotFoundException("Hacker group not found")
        return group

    def generate_group_code(self):
        code = ""
        while True:
            code = generate_random_code(10)
            code_exists = self.get_by_code(code, False)
            if code_exists is None:
                break
        return code

    def get_hacker_group(self, id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER, UserType.HACKER]):
            raise AuthorizationException("Not authorized")
        group = self.get_by_id(id)
        members_ids = [h.id for h in group.members]
        if data.check([UserType.HACKER, UserType.LLEIDAHACKER]) and (
            data.is_admin or data.user_id in members_ids
        ):
            return HackerGroupGetAll.model_validate(group)
        return HackerGroupGet.model_validate(group)

    @BaseService.needs_service(EventService)
    @BaseService.needs_service(HackerService)
    def add_hacker_group(self, payload: HackerGroupCreate, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER, UserType.HACKER]):
            raise AuthorizationException("Not authorized")
        if not data.check([UserType.LLEIDAHACKER]) and data.user_id != payload.leader_id:
            raise AuthorizationException("Not authorized")
        leader = self.lock_hacker(payload.leader_id)
        event = self.event_service.get_by_id(payload.event_id)
        if event.archived or not event.is_open:
            raise InvalidDataException("Event is not open for group registration")
        if leader not in event.registered_hackers:
            raise InvalidDataException("Hacker not registered to event")
        if any(group.event_id == event.id for group in leader.groups):
            raise InvalidDataException("Hacker already in a group")
        if event.max_group_size < 1:
            raise InvalidDataException("Group is full")
        new_hacker_group = HackerGroup(
            **payload.model_dump(), code=self.generate_group_code(), members=[leader]
        )
        db.session.add(new_hacker_group)
        db.session.commit()
        db.session.refresh(new_hacker_group)
        return new_hacker_group

    def update_hacker_group(self, id: int, payload: HackerGroupUpdate, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER, UserType.HACKER]):
            raise AuthorizationException("Not authorized")
        hacker_group = self.get_for_update(id)
        if not self.can_manage(hacker_group, data):
            raise AuthorizationException("Not authorized")
        if "leader_id" in payload.model_fields_set:
            self.validate_leader(hacker_group, payload.leader_id)
        updated = set_existing_data(hacker_group, payload)
        db.session.commit()
        return hacker_group, updated

    def delete_hacker_group(self, id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER, UserType.HACKER]):
            raise AuthorizationException("Not authorized")
        hacker_group = self.get_for_update(id)
        if not self.can_manage(hacker_group, data):
            raise AuthorizationException("Not authorized")
        db.session.query(HackerGroupUser).filter(
            HackerGroupUser.group_id == id
        ).delete()
        db.session.delete(hacker_group)
        db.session.commit()
        return hacker_group

    def _add_hacker_to_group(self, group, hacker, event):
        if event.archived or not event.is_open:
            raise InvalidDataException("Event is not open for group registration")
        if hacker in group.members:
            raise InvalidDataException("Hacker already in group")
        if hacker not in event.registered_hackers:
            raise InvalidDataException("Hacker not registered")
        if any(item.event_id == event.id for item in hacker.groups):
            raise InvalidDataException("Hacker already in a group")
        if len(group.members) >= event.max_group_size:
            raise InvalidDataException("Group is full")
        group.members.append(hacker)
        db.session.commit()
        db.session.refresh(group)

    @BaseService.needs_service(HackerService)
    @BaseService.needs_service(EventService)
    def add_hacker_to_group(self, groupId: int, hackerId: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthorizationException("Not authorized")
        hacker = self.lock_hacker(hackerId)
        group = self.get_for_update(groupId)
        event = self.event_service.get_by_id(group.event_id)
        self._add_hacker_to_group(group, hacker, event)
        return group

    @BaseService.needs_service(EventService)
    @BaseService.needs_service(HackerService)
    def add_hacker_to_group_by_code(self, code: str, hackerId: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]) and not data.check(
            [UserType.HACKER], hackerId
        ):
            raise AuthorizationException("Not authorized")
        hacker = self.lock_hacker(hackerId)
        group = self.get_for_update(self.get_by_code(code).id)

        event = self.event_service.get_by_id(group.event_id)
        self._add_hacker_to_group(group, hacker, event)
        return group

    def remove_hacker_from_group(self, groupId: int, hackerId: int, data: BaseToken):
        deleted = False
        if not data.check([UserType.LLEIDAHACKER, UserType.HACKER]):
            raise AuthorizationException("Not authorized")
        hacker_group = self.get_for_update(groupId)
        if not self.can_manage(hacker_group, data) and not data.check([UserType.HACKER], hackerId):
            raise AuthorizationException("Not authorized")
        hacker = [member for member in hacker_group.members if member.id == hackerId]
        if not hacker:
            raise NotFoundException("Hacker is not a member of this group")
        hacker_group.members.remove(hacker[0])
        if len(hacker_group.members) == 0:
            db.session.delete(hacker_group)
            deleted = True
        elif hacker_group.leader_id == hackerId:
            hacker_group.leader_id = hacker_group.members[0].id
        db.session.commit()
        if not deleted:
            db.session.refresh(hacker_group)
        return hacker_group

    @BaseService.needs_service(HackerService)
    def set_hacker_group_leader(self, groupId: int, hackerId: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER, UserType.HACKER]):
            raise AuthorizationException("Not authorized")
        hacker_group = self.get_for_update(groupId)
        hacker = self.hacker_service.get_by_id(hackerId)
        if hacker_group.leader_id == hacker.id:
            raise InvalidDataException("Cannot set leader to current leader")
        if not self.can_manage(hacker_group, data):
            raise AuthorizationException("Not authorized")
        self.validate_leader(hacker_group, hackerId)
        hacker_group.leader_id = hacker.id
        db.session.commit()
        db.session.refresh(hacker_group)
        return hacker_group
