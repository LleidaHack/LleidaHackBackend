from datetime import datetime as date

from fastapi_sqlalchemy import db

from src.error.AuthenticationException import AuthenticationException
from src.error.InvalidDataException import InvalidDataException
from src.error.NotFoundException import NotFoundException
from src.impl.Event.model import HackerAccepted as ModelHackerAccepted
from src.impl.Event.model import \
    HackerParticipation as ModelHackerParticipation
from src.impl.Event.model import HackerRegistration as ModelHackerRegistration
from src.impl.Hacker.model import Hacker as ModelHacker
from src.impl.Hacker.schema import HackerGet as HackerCreateSchema
from src.impl.Hacker.schema import HackerGet as HackerGetSchema
from src.impl.Hacker.schema import HackerGetAll as HackerGetAllSchema
from src.impl.Hacker.schema import HackerUpdate as HackerUpdateSchema
from src.impl.HackerGroup.model import HackerGroupUser as ModelHackerGroupUser
from src.utils.Base.BaseService import \
    BaseService  # an object to provide global access to a database session
from src.utils.security import get_password_hash
from src.utils.service_utils import (check_image, check_user,
                                     generate_user_code, set_existing_data)
from src.utils.Token import BaseToken
from src.utils.UserType import UserType


class HackerService(BaseService):
    name = 'hacker_service'

    def get_all(self):
        return db.session.query(ModelHacker).all()

    def get_by_id(self, hacker_id: int):
        user = db.session.query(ModelHacker).filter(
            ModelHacker.id == hacker_id).first()
        if user is None:
            raise NotFoundException("Hacker not found")
        return user

    def get_by_code(self, code: str):
        event = db.session.query(ModelHacker).filter(
            ModelHacker.code == code).first()
        if event is None:
            raise NotFoundException('hacker not found')
        return event

    def get_hacker(self, hackerId: int, data: BaseToken):
        user = self.get_by_id(hackerId)
        if data.check([UserType.LLEIDAHACKER, UserType.HACKER], hackerId):
            return HackerGetAllSchema.from_orm(user)
        return HackerGetSchema.from_orm(user)

    def get_hacker_by_code(self, code: str):
        user = db.session.query(ModelHacker).filter(
            ModelHacker.code == code).first()
        if user is None:
            raise NotFoundException("Hacker not found")
        return user

    def get_hacker_by_email(self, email: str):
        user = db.session.query(ModelHacker).filter(
            ModelHacker.email == email).first()
        if user is None:
            raise NotFoundException("Hacker not found")
        return user

    def add_hacker(self, payload: HackerCreateSchema):
        check_user(payload.email, payload.nickname, payload.telephone)
        new_hacker = ModelHacker(**payload.dict(), code=generate_user_code())
        if payload.image is not None:
            payload = check_image(payload)
        new_hacker.password = get_password_hash(payload.password)

        db.session.add(new_hacker)
        db.session.commit()
        db.session.refresh(new_hacker)
        db.session.flush()
        return new_hacker

    def remove_hacker(self, hackerId: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]) or not data.check(
            [UserType.HACKER], hackerId):
            raise AuthenticationException("Not authorized")
        hacker = self.get_by_id(hackerId)
        hacker_groups_ids = db.session.query(ModelHackerGroupUser).filter(
            ModelHackerGroupUser.hacker_id == hackerId).all()
        hacker_groups_ids = [group.group_id for group in hacker_groups_ids]
        hacker_groups = self.hackergroup_service.get_when_id_in(
            hacker_groups_ids)
        event_regs = db.session.query(ModelHackerRegistration).filter(
            ModelHackerRegistration.user_id == hackerId).all()
        for event_reg in event_regs:
            db.session.delete(event_reg)
        event_parts = db.session.query(ModelHackerParticipation).filter(
            ModelHackerParticipation.user_id == hackerId).all()
        for event_part in event_parts:
            db.session.delete(event_part)
        event_accs = db.session.query(ModelHackerAccepted).filter(
            ModelHackerAccepted.user_id == hackerId).all()
        for event_acc in event_accs:
            db.session.delete(event_acc)
        db.session.delete(hacker)
        for group in hacker_groups:
            if len(group.members) <= 1:
                db.session.delete(group)
            else:
                if group.leader_id == hackerId:
                    members_ids = [h.id for h in group.members]
                    members_ids.remove(hackerId)
                    group.leader_id = members_ids[0]
                # db.session.delete(hacker_group_user)
        db.session.commit()
        return hacker

    def update_hacker(self, hackerId: int, payload: HackerUpdateSchema,
                      data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]) or not data.check(
            [UserType.HACKER], hackerId):
            raise AuthenticationException("Not authorized")
        hacker = self.get_by_id(hackerId)
        if payload.image is not None:
            payload = check_image(payload)
        updated = set_existing_data(hacker, payload)
        hacker.updated_at = date.now()
        updated.append("updated_at")
        if payload.password is not None:
            hacker.password = get_password_hash(payload.password)
        db.session.commit()
        db.session.refresh(hacker)
        return hacker, updated

    def ban_hacker(self, hackerId: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        hacker = self.get_by_id(hackerId)
        if hacker.banned:
            raise InvalidDataException("Hacker already banned")
        hacker.banned = True
        db.session.commit()
        db.session.refresh(hacker)
        return hacker

    def unban_hacker(self, hackerId: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        hacker = self.get_by_id(hackerId)
        if not hacker.banned:
            raise InvalidDataException("Hacker already unbanned")
        hacker.banned = False
        db.session.commit()
        db.session.refresh(hacker)
        return hacker

    #TODO: #34 Check if token validation is correct
    def get_hacker_events(self, hackerId: int):
        hacker = self.get_by_id(hackerId)
        return hacker.events

    #TODO: #34 Check if token validation is correct
    def get_hacker_groups(self, hackerId: int):
        hacker = self.get_by_id(hackerId)
        return hacker.groups

    # def register_hacker_to_event(self, payload: EventRegistrationSchema, hacker_id: int, event_id: int, data: BaseToken):
    #     if not data.is_admin:
    #         if not (data.available and (data.type == UserType.LLEIDAHACKER.value or
    #                                     (data.type == UserType.HACKER.value
    #                                     and data.user_id == hacker_id))):
    #             raise AuthenticationException("Not authorized")
    #     event = self.event_service.get_by_id(event_id)
    #     if not event.is_open:
    #         raise InvalidDataException("Event registration not open")
    #     hacker = self.get_by_id(hacker_id)
    #     if hacker in event.registered_hackers or hacker in event.accepted_hackers:
    #         raise InvalidDataException("Hacker already registered")
    #     if len(event.registered_hackers) >= event.max_participants:
    #         raise InvalidDataException("Event full")
    #     if payload.cv != "" and not isBase64(payload.cv):
    #         raise InvalidDataException("Invalid CV")
    #     event_registration = ModelHackerRegistration(**payload.dict(),
    #                                                 user_id=hacker.id,
    #                                                 event_id=event.id,
    #                                                 confirmed_assistance=False,
    #                                                 confirm_assistance_token="")
    #     if payload.update_user:
    #         if hacker.cv != payload.cv:
    #             hacker.cv = payload.cv
    #         # if hacker.description != payload.description:
    #         #     hacker.description = payload.description
    #         if hacker.food_restrictions != payload.food_restrictions:
    #             hacker.food_restrictions = payload.food_restrictions
    #         if hacker.shirt_size != payload.shirt_size:
    #             hacker.shirt_size = payload.shirt_size
    #         if hacker.github != payload.github:
    #             hacker.github = payload.github
    #         if hacker.linkedin != payload.linkedin:
    #             hacker.linkedin = payload.linkedin
    #         if hacker.studies != payload.studies:
    #             hacker.studies = payload.studies
    #         if hacker.study_center != payload.study_center:
    #             hacker.study_center = payload.study_center
    #         if hacker.location != payload.location:
    #             hacker.location = payload.location
    #         if hacker.how_did_you_meet_us != payload.how_did_you_meet_us:
    #             hacker.how_did_you_meet_us = payload.how_did_you_meet_us
    #     db.session.add(event_registration)
    #     db.session.commit()
    #     db.session.refresh(event)
    #     db.session.refresh(hacker)
    #     send_event_registration_email(hacker, event)
    #     return event

    # def unregister_hacker_from_event(event: ModelEvent, hacker: ModelHacker,
    #                                 db.session: Session, data: BaseToken):
    #     if not data.is_admin:
    #         if not (data.available and (data.type == UserType.LLEIDAHACKER.value or
    #                                     (data.type == UserType.HACKER.value
    #                                     and data.user_id == hacker.id))):
    #             raise AuthenticationException("Not authorized")
    #     if not event.is_open:
    #         raise InvalidDataException("Event registration not open")
    #     if not (hacker in event.registered_hackers
    #             or hacker in event.accepted_hackers):
    #         raise InvalidDataException("Hacker not registered")
    #     if hacker in event.participants:
    #         raise InvalidDataException("Hacker already participating")
    #     if hacker in event.accepted_hackers:
    #         event.accepted_hackers.remove(hacker)
    #     else:
    #         event.registered_hackers.remove(hacker)
    #     db.session.commit()
    #     db.session.refresh(event)
    #     return event

    # def update_all_codes(data: BaseToken):
    #     if not data.is_admin:
    #         raise AuthenticationException("Not authorized")
    #     hackers = db.session.query(ModelHacker).all()
    #     for hacker in hackers:
    #         hacker.code = generate_user_code(
    #             db.session
    #         )  # Assuming generate_new_code() is a function that generates a new code
    #     db.session.commit()
