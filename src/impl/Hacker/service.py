from datetime import datetime as date
from pydantic import parse_obj_as

from security import get_password_hash
from src.utils.Base.BaseService import BaseService

from src.utils.service_utils import set_existing_data, check_image, generate_user_code

from src.error.AuthenticationException import AuthenticationException
from src.error.NotFoundException import NotFoundException
from src.error.InvalidDataException import InvalidDataException

from src.utils.service_utils import check_user
from src.utils.TokenData import TokenData
from src.utils.UserType import UserType

from src.impl.Hacker.model import Hacker as ModelHacker
from src.impl.HackerGroup.model import HackerGroup as ModelHackerGroup
from src.impl.HackerGroup.model import HackerGroupUser as ModelHackerGroupUser
from src.impl.Event.model import HackerRegistration as ModelHackerRegistration
from src.impl.Event.model import HackerParticipation as ModelHackerParticipation
from src.impl.Event.model import HackerAccepted as ModelHackerAccepted

from src.impl.Hacker.schema import HackerGet as HackerCreateSchema
from src.impl.Hacker.schema import HackerUpdate as HackerUpdateSchema
from src.impl.Hacker.schema import HackerGet as HackerGetSchema
from src.impl.Hacker.schema import HackerGetAll as HackerGetAllSchema


class HackerService(BaseService):

    def get_all(self):
        return self.db.query(ModelHacker).all()

    def get_hacker(self, hackerId: int, data: TokenData):
        user = self.db.query(ModelHacker).filter(
            ModelHacker.id == hackerId).first()
        if user is None:
            raise NotFoundException("Hacker not found")
        if data.is_admin or (data.available and
                             (data.type == UserType.LLEIDAHACKER.value or
                              (data.type == UserType.HACKER.value
                               and data.user_id == hackerId))):
            return parse_obj_as(HackerGetAllSchema, user)
        return parse_obj_as(HackerGetSchema, user)

    def get_hacker_by_code(self, code: str):
        user = self.db.query(ModelHacker).filter(
            ModelHacker.code == code).first()
        if user is None:
            raise NotFoundException("Hacker not found")
        return user

    def get_hacker_by_email(self, email: str):
        user = self.db.query(ModelHacker).filter(
            ModelHacker.email == email).first()
        if user is None:
            raise NotFoundException("Hacker not found")
        return user

    def add_hacker(self, payload: HackerCreateSchema):
        check_user(payload.email, payload.nickname, payload.telephone)
        new_hacker = ModelHacker(**payload.dict(),
                                 code=generate_user_code())
        if payload.image is not None:
            payload = check_image(payload)
        new_hacker.password = get_password_hash(payload.password)

        self.db.add(new_hacker)
        self.db.commit()
        self.db.refresh(new_hacker)
        return new_hacker

    def remove_hacker(self, hackerId: int, data: TokenData):
        if not data.is_admin:
            if not (
                    data.available and
                (data.type == UserType.LLEIDAHACKER.value or
                 (data.type == UserType.HACKER and data.user_id == hackerId))):
                raise AuthenticationException("Not authorized")
        hacker = self.db.query(ModelHacker).filter(
            ModelHacker.id == hackerId).first()
        if not hacker:
            raise NotFoundException("Hacker not found")
        hacker_groups_ids = self.db.query(ModelHackerGroupUser).filter(
            ModelHackerGroupUser.hacker_id == hackerId).all()
        hacker_groups_ids = [group.group_id for group in hacker_groups_ids]
        hacker_groups = self.db.query(ModelHackerGroup).filter(
            ModelHackerGroup.id.in_(hacker_groups_ids)).all()

        event_regs = self.db.query(ModelHackerRegistration).filter(
            ModelHackerRegistration.user_id == hackerId).all()
        for event_reg in event_regs:
            self.db.delete(event_reg)
        event_parts = self.db.query(ModelHackerParticipation).filter(
            ModelHackerParticipation.user_id == hackerId).all()
        for event_part in event_parts:
            self.db.delete(event_part)
        event_accs = self.db.query(ModelHackerAccepted).filter(
            ModelHackerAccepted.user_id == hackerId).all()
        for event_acc in event_accs:
            self.db.delete(event_acc)
        self.db.delete(hacker)
        for group in hacker_groups:
            # hacker_group_user = self.db.query(ModelHackerGroupUser).filter(
            #     ModelHackerGroupUser.hacker_id == hackerId
            #     and ModelHackerGroupUser.group_id == group.id).first()
            if len(group.members) <= 1:
                self.db.delete(group)
            else:
                if group.leader_id == hackerId:
                    members_ids = [h.id for h in group.members]
                    members_ids.remove(hackerId)
                    group.leader_id = members_ids[0]
                # self.db.delete(hacker_group_user)
        self.db.commit()
        return hacker

    def update_hacker(self, hackerId: int, payload: HackerUpdateSchema,
                      data: TokenData):
        if not data.is_admin:
            if not (data.available and
                    (data.type == UserType.LLEIDAHACKER.value or
                     (data.type == UserType.HACKER.value
                      and data.user_id == hackerId))):
                raise AuthenticationException("Not authorized")
        hacker = self.db.query(ModelHacker).filter(
            ModelHacker.id == hackerId).first()
        if hacker is None:
            raise NotFoundException("Hacker not found")
        if payload.image is not None:
            payload = check_image(payload)
        updated = set_existing_data(hacker, payload)
        hacker.updated_at = date.now()
        updated.append("updated_at")
        if payload.password is not None:
            hacker.password = get_password_hash(payload.password)
        self.db.commit()
        self.db.refresh(hacker)
        return hacker, updated

    def ban_hacker(self, hackerId: int, data: TokenData):
        if not data.is_admin:
            if not (data.available
                    and data.type == UserType.LLEIDAHACKER.value):
                raise AuthenticationException("Not authorized")
        hacker = self.db.query(ModelHacker).filter(
            ModelHacker.id == hackerId).first()
        if hacker is None:
            raise NotFoundException("Hacker not found")
        if hacker.banned:
            raise InvalidDataException("Hacker already banned")
        hacker.banned = 1
        self.db.commit()
        self.db.refresh(hacker)
        return hacker

    def unban_hacker(self, hackerId: int, data: TokenData):
        if not data.is_admin:
            if not (data.available
                    and data.type == UserType.LLEIDAHACKER.value):
                raise AuthenticationException("Not authorized")
        hacker = self.db.query(ModelHacker).filter(
            ModelHacker.id == hackerId).first()
        if hacker is None:
            raise NotFoundException("Hacker not found")
        if not hacker.banned:
            raise InvalidDataException("Hacker already unbanned")
        hacker.banned = 0
        self.db.commit()
        self.db.refresh(hacker)
        return hacker

    #TODO: #34 Check if token validation is correct
    def get_hacker_events(self, hackerId: int):
        hacker = self.db.query(ModelHacker).filter(
            ModelHacker.id == hackerId).first()
        if hacker is None:
            raise NotFoundException("Hacker not found")
        return hacker.events

    #TODO: #34 Check if token validation is correct
    def get_hacker_groups(self, hackerId: int):
        hacker = self.db.query(ModelHacker).filter(
            ModelHacker.id == hackerId).first()
        if hacker is None:
            raise NotFoundException("Hacker not found")
        return hacker.groups

    # def update_all_codes(data: TokenData):
    #     if not data.is_admin:
    #         raise AuthenticationException("Not authorized")
    #     hackers = self.db.query(ModelHacker).all()
    #     for hacker in hackers:
    #         hacker.code = generate_user_code(
    #             db
    #         )  # Assuming generate_new_code() is a function that generates a new code
    #     self.db.commit()
