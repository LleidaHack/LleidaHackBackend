from pydantic import parse_obj_as
from sqlalchemy.orm import Session

from src.utils.TokenData import TokenData
from src.utils.UserType import UserType
from utils.BaseService import BaseService

from utils.service_utils import set_existing_data, check_image

from src.error.AuthenticationException import AuthenticationException
from src.error.NotFoundException import NotFoundException

from src.impl.Event.schema import EventCreate as EventCreateSchema
from src.impl.Event.schema import EventUpdate as EventUpdateSchema
from src.impl.Event.schema import EventGet as EventGetSchema
from src.impl.Event.schema import EventGetAll as EventGetAllSchema
from src.impl.Hacker.schema import HackerGetAll as HackerGetAllSchema

from src.impl.Event.model import Event as ModelEvent
from src.impl.Company.model import Company as ModelCompany
from src.impl.Hacker.model import Hacker as ModelHacker
from src.impl.HackerGroup.model import HackerGroup as ModelHackerGroup
from src.impl.HackerGroup.model import HackerGroupUser as ModelHackerGroupUser


class EventService(BaseService):

    def get_all(self):
        return self.db.query(ModelEvent).all()

    def get_hackeps(self, year: int):
        #return and event called HackEPS year ignoring caps
        e = self.db.query(ModelEvent).filter(
            ModelEvent.name.ilike(f'%HackEPS {str(year)}%')).first()
        if e is None:
            return self.db.query(ModelEvent).filter(
                ModelEvent.name.ilike(f'%HackEPS {str(year-1)}%')).first()
        return e

    def get_hacker_group(self, event_id: int, hacker_id: int, data: TokenData):
        event = self.db.query(ModelEvent).filter(
            ModelEvent.id == event_id).first()
        if event is None:
            raise NotFoundException("Event not found")
        hacker = self.db.query(ModelHacker).filter(
            ModelHacker.id == hacker_id).first()
        if hacker is None:
            raise NotFoundException("Hacker not found")
        if hacker not in event.registered_hackers:
            raise NotFoundException("Hacker is not participant")
        user_groups = self.db.query(ModelHackerGroupUser).filter(
            ModelHackerGroupUser.hacker_id == hacker_id).all()
        group = self.db.query(ModelHackerGroup).filter(
            ModelHackerGroup.event_id == event_id).filter(
                ModelHackerGroup.id.in_(
                    [g.hacker_group_id for g in user_groups])).first()
        return group

    def get_event(self, id: int, data: TokenData):
        event = self.db.query(ModelEvent).filter(ModelEvent.id == id).first()
        if data.is_admin or (data.available
                             and data.type == UserType.LLEIDAHACKER.value):
            return parse_obj_as(EventGetAllSchema, event)
        return parse_obj_as(EventGetSchema, event)

    def add_event(self, payload: EventCreateSchema, data: TokenData):
        if not data.is_admin:
            if not (data.available
                    and data.type == UserType.LLEIDAHACKER.value):
                raise AuthenticationException("Not authorized")
        if payload.image is not None:
            payload = check_image(payload)
        db_event = ModelEvent(**payload.dict())
        self.db.add(db_event)
        self.db.commit()
        self.db.refresh(db_event)
        return db_event

    def update_event(self, id: int, event: EventUpdateSchema, data: TokenData):
        if not data.is_admin:
            if not (data.available
                    and data.type == UserType.LLEIDAHACKER.value):
                raise AuthenticationException("Not authorized")
        db_event = self.db.query(ModelEvent).filter(
            ModelEvent.id == id).first()
        if db_event is None:
            raise NotFoundException("Event not found")
        if event.image is not None:
            event = check_image(event)
        updated = set_existing_data(db_event, event)
        self.db.commit()
        return db_event, updated

    def delete_event(self, id: int, data: TokenData):
        if not data.is_admin:
            if not (data.available
                    and data.type == UserType.LLEIDAHACKER.value):
                raise AuthenticationException("Not authorized")
        db_event = self.db.query(ModelEvent).filter(
            ModelEvent.id == id).first()
        if db_event is None:
            raise NotFoundException("Event not found")
        self.db.delete(db_event)
        self.db.commit()
        return db_event

    def is_registered(self, id: int, hacker_id: int, data: TokenData):
        event = self.db.query(ModelEvent).filter(ModelEvent.id == id).first()
        if event is None:
            raise NotFoundException("Event not found")
        hacker = self.db.query(ModelHacker).filter(
            ModelHacker.id == hacker_id).first()
        if hacker is None:
            raise NotFoundException("Hacker not found")
        return hacker in event.registered_hackers

    def is_accepted(self, id: int, hacker_id: int, data: TokenData):
        event = self.db.query(ModelEvent).filter(ModelEvent.id == id).first()
        if event is None:
            raise NotFoundException("Event not found")
        hacker = self.db.query(ModelHacker).filter(
            ModelHacker.id == hacker_id).first()
        if hacker is None:
            raise NotFoundException("Hacker not found")
        return hacker in event.accepted_hackers

    def get_event_meals(self, id: int, data: TokenData):
        event = self.db.query(ModelEvent).filter(ModelEvent.id == id).first()
        if event is None:
            raise NotFoundException("Event not found")
        return event.meals

    def get_event_participants(self, id: int, data: TokenData):
        event = self.db.query(ModelEvent).filter(ModelEvent.id == id).first()
        if event is None:
            raise NotFoundException("Event not found")
        return event.registered_hackers

    def get_event_sponsors(self, id: int):
        event = self.db.query(ModelEvent).filter(ModelEvent.id == id).first()
        if event is None:
            raise NotFoundException("Event not found")
        return event.sponsors

    def get_event_groups(self, id: int, data: TokenData):
        event = self.db.query(ModelHackerGroup).filter(
            ModelHackerGroup.event_id == id)
        if event is None:
            raise NotFoundException("Event not found")
        return event

    def add_company(self, id: int, company_id: int, data: TokenData):
        if not data.is_admin:
            if not (data.available
                    and data.type == UserType.LLEIDAHACKER.value):
                raise Exception("Not authorized")
        event = self.db.query(ModelEvent).filter(ModelEvent.id == id).first()
        if event is None:
            raise Exception("Event not found")
        company = self.db.query(ModelCompany).filter(
            ModelCompany.id == company_id).first()
        if company is None:
            raise Exception("Company not found")
        event.sponsors.append(company)
        self.db.commit()
        self.db.refresh(event)
        self.db.refresh(company)
        return event

    # def add_hacker(id: int, hacker_id: int, db: Session, data: TokenData):
    #     if not data.is_admin:
    #         if not (data.available and (data.type == UserType.LLEIDAHACKER.value or
    #                                     (data.type == UserType.HACKER.value
    #                                      and hacker_id != data.user_id))):
    #             raise Exception("Not authorized")
    #     event = db.query(ModelEvent).filter(ModelEvent.id == id).first()
    #     if event is None:
    #         raise Exception("Event not found")
    #     hacker = db.query(ModelHacker).filter(ModelHacker.id == hacker_id).first()
    #     if hacker is None:
    #         raise Exception("Hacker not found")
    #     if not data.is_admin:
    #         if event.max_participants <= len(event.hackers):
    #             raise Exception("Event is full")
    #     event.hackers.append(hacker)
    #     db.commit()
    #     db.refresh(event)
    #     db.refresh(hacker)
    #     return event

    def add_hacker_group(self, id: int, hacker_group_id: int, data: TokenData):
        if not data.is_admin:
            if not (data.available and
                    (data.type == UserType.LLEIDAHACKER.value
                     or data.type == UserType.HACKER.value)):
                raise Exception("Not authorized")
        hacker_group = self.db.query(ModelHackerGroup).filter(
            ModelHackerGroup.id == hacker_group_id).first()
        grou_hackers = [hacker.id for hacker in hacker_group.hackers]
        if not data.is_admin:
            if data.user_id not in grou_hackers or hacker_group.leader_id != data.user_id:
                raise Exception("Not authorized")
        if hacker_group is None:
            raise Exception("Hacker group not found")
        event = self.db.query(ModelEvent).filter(ModelEvent.id == id).first()
        if event is None:
            raise Exception("Event not found")
        if not data.is_admin:
            if event.max_participants <= len(event.hackers) + len(
                    hacker_group.hackers):
                raise Exception("Event is full")
        event.hacker_groups.append(hacker_group)
        event.hackers.extend(hacker_group.hackers)
        self.db.commit()
        self.db.refresh(event)
        return event

    def remove_company(self, id: int, company_id: int, data: TokenData):
        if not data.is_admin:
            if not (data.available
                    and data.type == UserType.LLEIDAHACKER.value):
                raise Exception("Not authorized")
        company = self.db.query(ModelCompany).filter(
            ModelCompany.id == company_id).first()
        if company is None:
            raise Exception("Company not found")
        company_users = [user.id for user in company.users]
        if not data.is_admin:
            if data.user_id not in company_users:
                raise Exception("Not authorized")
        event = self.db.query(ModelEvent).filter(ModelEvent.id == id).first()
        if event is None:
            raise Exception("Event not found")
        if company not in event.companies:
            raise Exception("Company is not sponsor")
        event.companies.remove(company)
        self.db.commit()
        self.db.refresh(event)
        self.db.refresh(company)
        return event

        # def remove_hacker(id: int, hacker_id: int, db: Session, data: TokenData):
        #     if not data.is_admin:
        #         if not (data.available and (data.type == UserType.LLEIDAHACKER.value or
        #                                     (data.type == UserType.HACKER.value
        #                                      and hacker_id != data.user_id))):
        #             raise Exception("Not authorized")
        #     event = db.query(ModelEvent).filter(ModelEvent.id == id).first()
        #     if event is None:
        #         raise Exception("Event not found")
        #     hacker = db.query(ModelHacker).filter(ModelHacker.id == hacker_id).first()
        #     if hacker is None:
        #         raise Exception("Hacker not found")
        #     if hacker not in event.hackers:
        #         raise Exception("Hacker is not participant")
        #     event.hackers.remove(hacker)
        #     hacker_group = db.query(ModelHackerGroup).filter(
        #         ModelHackerGroup.id == hacker.hacker_group_id).first()
        #     if hacker_group is not None:
        #         hacker_group.hackers.remove(hacker)
        #     db.commit()
        #     db.refresh(hacker_group)
        #     db.refresh(hacker)
        #     db.refresh(event)
        return event

    def remove_hacker_group(self, id: int, hacker_group_id: int,
                            data: TokenData):
        if not data.is_admin:
            if not (data.available and
                    (data.type == UserType.LLEIDAHACKER.value
                     or data.type == UserType.HACKER.value)):
                raise Exception("Not authorized")
        hacker_group = self.db.query(ModelHackerGroup).filter(
            ModelHackerGroup.id == hacker_group_id).first()
        if hacker_group is None:
            raise Exception("Hacker group not found")
        group_hackers = [hacker.id for hacker in hacker_group.members]
        if not data.is_admin:
            if data.user_id not in group_hackers or hacker_group.leader_id != data.user_id:
                raise Exception("Not authorized")
        event = self.db.query(ModelEvent).filter(ModelEvent.id == id).first()
        if event is None:
            raise Exception("Event not found")
        event.hacker_groups.remove(hacker_group)
        for hacker in hacker_group.members:
            event.registered_hackers.remove(hacker)
        self.db.commit()
        self.db.refresh(hacker_group)
        self.db.refresh(event)
        return event

    def get_accepted_hackers(self, event_id: int, data: TokenData):
        if not data.is_admin:
            if not (data.available
                    and data.type == UserType.LLEIDAHACKER.value):
                raise Exception("Not authorized")
        event = self.db.query(ModelEvent).filter(
            ModelEvent.id == event_id).first()
        if event is None:
            raise Exception("Event not found")
        hackers = []
        for h in event.accepted_hackers:
            hackers.append(h)
        return parse_obj_as(HackerGetAllSchema, hackers)

    def get_accepted_hackers_mails(self, event_id: int, data: TokenData):
        if not data.is_admin:
            if not (data.available
                    and data.type == UserType.LLEIDAHACKER.value):
                raise Exception("Not authorized")
        event = self.db.query(ModelEvent).filter(
            ModelEvent.id == event_id).first()
        if event is None:
            raise Exception("Event not found")
        hackers = []
        for h in event.accepted_hackers:
            hackers.append(h.email)
        return parse_obj_as(HackerGetAllSchema, hackers)
