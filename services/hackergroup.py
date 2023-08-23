from models.Hacker import HackerGroup as ModelHackerGroup
from models.Hacker import HackerGroupUser as ModelHackerGroupUser
from models.Hacker import Hacker as ModelHacker
from models.TokenData import TokenData
from models.UserType import UserType

from schemas.Hacker import HackerGroup as SchemaHackerGroup
from schemas.Hacker import HackerGroupUpdate as SchemaHackerGroupUpdate

from sqlalchemy.orm import Session

from utils.service_utils import generate_random_code, set_existing_data

from error.AuthenticationException import AuthenticationException
from error.NotFoundException import NotFoundException
from error.InvalidDataException import InvalidDataException


async def get_all(db: Session):
    return db.query(ModelHackerGroup).all()


async def get_group_by_code(code: str, db: Session):
    group = db.query(ModelHackerGroup).filter(
        ModelHackerGroup.code == code).first()
    if group is None:
        raise NotFoundException("Hacker group not found")
    return group


async def get_hacker_group(id: int, db: Session):
    group = db.query(ModelHackerGroup).filter(
        ModelHackerGroup.id == id).first()
    if group is None:
        raise NotFoundException("Hacker group not found")


async def add_hacker_group(payload: SchemaHackerGroup, hackerId: int,
                           db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and (data.type == UserType.LLEIDAHACKER.value
                                    or data.type == UserType.HACKER.value)):
            raise AuthenticationException("Not authorized")
    members = []
    if data.type == UserType.HACKER.value:
        hacker = db.query(ModelHacker).filter(
            ModelHacker.id == hackerId).first()
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
    if hacker_group.members is None:
        hacker_group.members = []
    hacker_group.members.append(hacker)
    db.commit()
    db.refresh(hacker_group)
    return hacker_group


async def remove_hacker_from_group(groupId: int, hackerId: int, db: Session,
                                   data: TokenData):
    if not data.is_admin:
        if not (data.available and (data.type == UserType.LLEIDAHACKER.value
                                    or data.type == UserType.HACKER.value)):
            raise AuthenticationException("Not authorized")
    hacker_group = db.query(ModelHackerGroup).filter(
        ModelHackerGroup.id == groupId).first()
    if hacker_group is None:
        raise NotFoundException("Hacker group not found")
    if hacker_group.leader_id == hackerId:
        raise InvalidDataException("Cannot remove leader from group")
    if not (data.type == UserType.HACKER.value
            and data.user_id == hacker_group.leader_id):
        raise AuthenticationException("Not authorized")
    hacker = [h for h in hacker_group.members if h.id == hackerId]
    hacker_group.members.remove(hacker[0])
    db.commit()
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
    if hacker_group.leader_id == hackerId:
        raise InvalidDataException("Cannot set leader to current leader")
    if not (data.type == UserType.HACKER.value
            and data.user_id == hacker_group.leader_id):
        raise AuthenticationException("Not authorized")
    hacker_group.leader_id = hackerId
    db.commit()
    db.refresh(hacker_group)
    return hacker_group
