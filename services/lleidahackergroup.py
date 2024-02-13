from src.LleidaHacker.model import LleidaHackerGroup as ModelLleidaHackerGroup
from src.LleidaHacker.model import LleidaHacker as ModelLleidaHacker
from src.Utils.TokenData import TokenData
from src.Utils.UserType import UserType

from src.LleidaHacker.schema import LleidaHackerGroup as SchemaLleidaHackerGroup
from src.LleidaHacker.schema import LleidaHackerGroupUpdate as SchemaLleidaHackerGroupUpdate

from utils.service_utils import set_existing_data

from sqlalchemy.orm import Session

from error.AuthenticationException import AuthenticationException
from error.NotFoundException import NotFoundException
from error.InvalidDataException import InvalidDataException


def get_all(db: Session):
    return db.query(ModelLleidaHackerGroup).all()


def get_lleidahackergroup(groupId: int, db: Session):
    group = db.query(ModelLleidaHackerGroup).filter(
        ModelLleidaHackerGroup.id == groupId).first()
    if group is None:
        raise NotFoundException("LleidaHacker group not found")
    return group


def add_lleidahackergroup(payload: SchemaLleidaHackerGroup, db: Session,
                                data: TokenData):
    if not data.is_admin:
        if not (data.available
                and data.user_type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    hacker = db.query(ModelLleidaHacker).filter(
        ModelLleidaHacker.id == data.user_id).first()
    if hacker is None:
        raise NotFoundException("LleidaHacker not found")
    new_lleidahacker_group = ModelLleidaHackerGroup(**payload.dict(),
                                                    leader_id=hacker.id)
    db.add(new_lleidahacker_group)
    db.commit()
    db.refresh(new_lleidahacker_group)
    return new_lleidahacker_group


def update_lleidahackergroup(groupId: int,
                                   payload: SchemaLleidaHackerGroupUpdate,
                                   db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available
                and data.user_type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    lleidahacker_group = db.query(ModelLleidaHackerGroup).filter(
        ModelLleidaHackerGroup.id == groupId).first()
    if lleidahacker_group is None:
        raise NotFoundException("LleidaHacker group not found")
    if not (data.user_type == UserType.LLEIDAHACKER.value
            and data.user_id == lleidahacker_group.leader_id):
        raise AuthenticationException("Not authorized")
    updated = set_existing_data(lleidahacker_group, payload)
    db.commit()
    db.refresh(lleidahacker_group)
    return lleidahacker_group, updated


def delete_lleidahackergroup(groupId: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available
                and data.user_type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    lleidahacker_group = db.query(ModelLleidaHackerGroup).filter(
        ModelLleidaHackerGroup.id == groupId).first()
    if lleidahacker_group is None:
        raise NotFoundException("LleidaHacker group not found")
    if not (data.user_type == UserType.LLEIDAHACKER.value
            and data.user_id == lleidahacker_group.leader_id):
        raise AuthenticationException("Not authorized")
    db.delete(lleidahacker_group)
    db.commit()
    return lleidahacker_group


def add_lleidahacker_to_group(groupId: int, lleidahackerId: int,
                                    db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available
                and data.user_type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    lleidahacker_group = db.query(ModelLleidaHackerGroup).filter(
        ModelLleidaHackerGroup.id == groupId).first()
    if lleidahacker_group is None:
        raise NotFoundException("LleidaHacker group not found")
    lleidahacker = db.query(ModelLleidaHacker).filter(
        ModelLleidaHacker.id == lleidahackerId).first()
    if not (data.user_type == UserType.LLEIDAHACKER.value
            and data.user_id == lleidahacker_group.leader_id):
        raise AuthenticationException("Not authorized")
    if lleidahacker is None:
        raise NotFoundException("LleidaHacker not found")
    lleidahacker_group.members.append(lleidahacker)
    db.commit()
    db.refresh(lleidahacker_group)
    return lleidahacker_group


def remove_lleidahacker_from_group(groupId: int, lleidahackerId: int,
                                         db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available
                and data.user_type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    lleidahacker_group = db.query(ModelLleidaHackerGroup).filter(
        ModelLleidaHackerGroup.id == groupId).first()
    if lleidahacker_group is None:
        raise NotFoundException("LleidaHacker group not found")
    if not (data.user_type == UserType.LLEIDAHACKER.value
            and data.user_id == lleidahacker_group.leader_id):
        raise AuthenticationException("Not authorized")
    lleidahacker = db.query(ModelLleidaHacker).filter(
        ModelLleidaHacker.id == lleidahackerId).first()
    if lleidahacker is None:
        raise NotFoundException("LleidaHacker not found")
    if lleidahacker not in lleidahacker_group.members:
        raise InvalidDataException("LleidaHacker not in group")
    lleidahacker_group.members.remove(lleidahacker)
    db.commit()
    db.refresh(lleidahacker_group)
    return lleidahacker_group


def set_lleidahacker_group_leader(groupId: int, lleidahackerId: int,
                                        db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available
                and data.user_type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    lleidahacker_group = db.query(ModelLleidaHackerGroup).filter(
        ModelLleidaHackerGroup.id == groupId).first()
    if lleidahacker_group is None:
        raise NotFoundException("LleidaHacker group not found")
    if not (data.user_type == UserType.LLEIDAHACKER.value
            and data.user_id == lleidahacker_group.leader_id):
        raise AuthenticationException("Not authorized")
    lleidahacker = db.query(ModelLleidaHacker).filter(
        ModelLleidaHacker.id == lleidahackerId).first()
    if lleidahacker is None:
        raise NotFoundException("LleidaHacker not found")
    if lleidahacker not in lleidahacker_group.members:
        raise InvalidDataException("LleidaHacker not in group")
    lleidahacker_group.leader_id = lleidahacker.id
    lleidahacker_group.leader = lleidahacker

    db.commit()
    db.refresh(lleidahacker_group)
    return lleidahacker_group
