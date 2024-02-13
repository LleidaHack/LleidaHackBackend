from src.Hacker.model import HackerGroup as ModelHackerGroup
from src.Hacker.model import HackerGroupUser as ModelHackerGroupUser
from src.Hacker.model import Hacker as ModelHacker
from src.Utils.TokenData import TokenData
from src.Utils.UserType import UserType
from src.Event.model import Event as ModelEvent

from src.Hacker.schema import HackerGroup as SchemaHackerGroup
from src.Hacker.schema import HackerGroupUpdate as SchemaHackerGroupUpdate

from sqlalchemy.orm import Session

from utils.service_utils import generate_random_code, set_existing_data

from error.AuthenticationException import AuthenticationException
from error.NotFoundException import NotFoundException
from error.InvalidDataException import InvalidDataException

from utils.hide_utils import hackergroup_show_private


async def get_all(db: Session):
    return db.query(ModelHackerGroup).all()


async def get_group_by_code(code: str, db: Session):
    group = db.query(ModelHackerGroup).filter(
        ModelHackerGroup.code == code).first()
    if group is None:
        raise NotFoundException("Hacker group not found")
    return group


async def get_hacker_group(id: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and (data.type == UserType.LLEIDAHACKER.value
                                    or data.type == UserType.HACKER.value)):
            raise AuthenticationException("Not authorized")
    group = db.query(ModelHackerGroup).filter(
        ModelHackerGroup.id == id).first()
    if group is None:
        raise NotFoundException("Hacker group not found")
    members_ids = [h.id for h in group.members]
    if data.is_admin or (data.type == UserType.HACKER.value
                         and data.user_id in members_ids
                         ) or data.type == UserType.LLEIDAHACKER.value:
        hackergroup_show_private(group)
    return group


async def add_hacker_group(payload: SchemaHackerGroup, db: Session,
                           data: TokenData):
    if not data.is_admin:
        if not (data.available and (data.type == UserType.LLEIDAHACKER.value
                                    or data.type == UserType.HACKER.value)):
            raise AuthenticationException("Not authorized")
    members = []
    event_exists = db.query(ModelEvent).filter(
        ModelEvent.id == payload.event_id).first()
    if event_exists is None:
        raise NotFoundException("Event not found")
    if data.type == UserType.HACKER.value:
        hacker = db.query(ModelHacker).filter(
            ModelHacker.id == data.user_id).first()
        if hacker is None:
            raise NotFoundException("Hacker not found")
        members.append(hacker)
    # generate a random 10 letter code
    code = ''
    while True:
        code = generate_random_code(10)
        code_exists = db.query(ModelHackerGroup).filter(
            ModelHackerGroup.code == code).first()
        if code_exists is None:
            break
    new_hacker_group = ModelHackerGroup(**payload.dict(),
                                        code=code,
                                        members=members)
    db.add(new_hacker_group)
    db.commit()
    db.refresh(new_hacker_group)
    return new_hacker_group


async def update_hacker_group(id: int, payload: SchemaHackerGroupUpdate,
                              db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and (data.type == UserType.LLEIDAHACKER.value
                                    or data.type == UserType.HACKER.value)):
            raise AuthenticationException("Not authorized")
    event_exists = db.query(ModelEvent).filter(
        ModelEvent.id == payload.event_id).first()
    if event_exists is None:
        raise NotFoundException("Event not found")
    hacker_group = db.query(ModelHackerGroup).filter(
        ModelHackerGroup.id == id).first()
    if hacker_group is None:
        raise NotFoundException("Hacker group not found")
    if not (data.type == UserType.HACKER.value
            and data.user_id == hacker_group.leader_id):
        raise AuthenticationException("Not authorized")
    updated = set_existing_data(hacker_group, payload)
    db.commit()
    return hacker_group, updated


async def delete_hacker_group(id: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and (data.type == UserType.LLEIDAHACKER.value
                                    or data.type == UserType.HACKER.value)):
            raise AuthenticationException("Not authorized")
    hacker_group = db.query(ModelHackerGroup).filter(
        ModelHackerGroup.id == id).first()
    if hacker_group is None:
        raise NotFoundException("Hacker group not found")
    if not (data.type == UserType.HACKER.value
            and data.user_id == hacker_group.leader_id):
        raise AuthenticationException("Not authorized")
    db.query(ModelHackerGroupUser).filter(
        ModelHackerGroupUser.group_id == id).delete()
    db.delete(hacker_group)
    db.commit()
    return hacker_group


async def add_hacker_to_group(groupId: int, hackerId: int, db: Session,
                              data: TokenData):
    if not data.is_admin:
        if not (data.available and (data.type == UserType.LLEIDAHACKER.value
                                    or data.type == UserType.HACKER.value)):
            raise AuthenticationException("Not authorized")
    hacker_group = db.query(ModelHackerGroup).filter(
        ModelHackerGroup.id == groupId).first()
    if hacker_group is None:
        raise NotFoundException("Hacker group not found")
    hacker = db.query(ModelHacker).filter(ModelHacker.id == hackerId).first()
    if hacker is None:
        raise NotFoundException("Hacker not found")
    # if hacker_group.members is None:
    #     hacker_group.members = []
    event = db.query(ModelEvent).filter(
        ModelEvent.id == hacker_group.event_id).first()
    if hacker not in event.registered_hackers:
        raise InvalidDataException("Hacker not registered")
    hacker_group_user = db.query(ModelHackerGroupUser).filter(
        ModelHackerGroupUser.hacker_id == hackerId).first()
    if hacker_group_user is not None:
        raise InvalidDataException("Hacker already in group")
    if len(hacker_group.members) >= event.max_group_size:
        raise InvalidDataException("Group is full")
    if hacker in hacker_group.members:
        raise InvalidDataException("Hacker already in group")
    hacker_group.members.append(hacker)
    db.commit()
    db.refresh(hacker_group)
    return hacker_group


async def add_hacker_to_group_by_code(code: str, hackerId: int, db: Session,
                                      data: TokenData):
    if not data.is_admin:
        if not (data.available and (data.type == UserType.LLEIDAHACKER.value or
                                    (data.type == UserType.HACKER.value
                                     and data.user_id == hackerId))):
            raise AuthenticationException("Not authorized")
    hacker_group = db.query(ModelHackerGroup).filter(
        ModelHackerGroup.code == code).first()
    if hacker_group is None:
        raise NotFoundException("Hacker group not found")
    hacker = db.query(ModelHacker).filter(ModelHacker.id == hackerId).first()
    if hacker is None:
        raise NotFoundException("Hacker not found")
    if hacker_group.members is None:
        hacker_group.members = []
    event = db.query(ModelEvent).filter(
        ModelEvent.id == hacker_group.event_id).first()
    if hacker not in event.registered_hackers:
        raise InvalidDataException("Hacker not registered")
    hacker_group_user = db.query(ModelHackerGroupUser).filter(
        ModelHackerGroupUser.hacker_id == hackerId).first()
    if hacker_group_user is not None:
        raise InvalidDataException("Hacker already in group")
    if len(hacker_group.members) >= event.max_group_size:
        raise InvalidDataException("Group is full")
    if hacker in hacker_group.members:
        raise InvalidDataException("Hacker already in group")
    hacker_group.members.append(hacker)
    db.commit()
    db.refresh(hacker_group)
    return hacker_group


async def remove_hacker_from_group(groupId: int, hackerId: int, db: Session,
                                   data: TokenData):
    deleted = False
    if not data.is_admin:
        if not (data.available and (data.type == UserType.LLEIDAHACKER.value
                                    or data.type == UserType.HACKER.value)):
            raise AuthenticationException("Not authorized")
    hacker_group = db.query(ModelHackerGroup).filter(
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
        db.delete(hacker_group)
        deleted = True
    elif hacker_group.leader_id == hackerId:
        hacker_group.leader_id = hacker_group.members[0].id
    db.commit()
    if not deleted:
        db.refresh(hacker_group)
    return hacker_group


async def set_hacker_group_leader(groupId: int, hackerId: int, db: Session,
                                  data: TokenData):
    if not data.is_admin:
        if not (data.available and (data.type == UserType.LLEIDAHACKER.value
                                    or data.type == UserType.HACKER.value)):
            raise AuthenticationException("Not authorized")
    hacker_group = db.query(ModelHackerGroup).filter(
        ModelHackerGroup.id == groupId).first()
    if hacker_group is None:
        raise NotFoundException("Hacker group not found")
    hacker = db.query(ModelHacker).filter(ModelHacker.id == hackerId).first()
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
    db.commit()
    db.refresh(hacker_group)
    return hacker_group
