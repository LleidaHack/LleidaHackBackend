from pydantic import parse_obj_as
from sqlalchemy.orm import Session

from src.utils.UserType import UserType
from src.utils.Base.BaseService import BaseService
from src.impl.Hacker.service import HackerService
# from src.impl.HackerGroup.service import HackerGroupService
from src.impl.Company.service import CompanyService

from src.utils.service_utils import set_existing_data, check_image, subtract_lists
from src.utils.Token import BaseToken

from src.error.AuthenticationException import AuthenticationException
from src.error.NotFoundException import NotFoundException

from src.impl.Event.schema import EventCreate as EventCreateSchema
from src.impl.Event.schema import EventUpdate as EventUpdateSchema
from src.impl.Event.schema import EventGet as EventGetSchema
from src.impl.Event.schema import EventGetAll as EventGetAllSchema
from src.impl.Hacker.schema import HackerGetAll as HackerGetAllSchema

from src.impl.Event.model import Event as ModelEvent
from src.impl.Event.model import HackerRegistration as ModelHackerRegistration
from src.impl.Event.model import HackerParticipation as ModelHackerParticipation
from src.impl.Company.model import Company as ModelCompany
from src.impl.Hacker.model import Hacker as ModelHacker
from src.impl.HackerGroup.model import HackerGroup as ModelHackerGroup
from src.impl.HackerGroup.model import HackerGroupUser as ModelHackerGroupUser


class EventService(BaseService):

    hacker_service = HackerService()
    company_service = CompanyService()
    # hackergroup_service = HackerGroupService()

    def get_all(self):
        return self.db.query(ModelEvent).all()
    
    def get_by_id(self, id: int) -> ModelEvent:
        event = self.db.query(ModelEvent).filter(ModelEvent.id == id).first()
        if event is None:
            raise NotFoundException('event not found')
        return event
    
    def get_hackeps(self, year: int):
        #return and event called HackEPS year ignoring caps
        e = self.db.query(ModelEvent).filter(
            ModelEvent.name.ilike(f'%HackEPS {str(year)}%')).first()
        if e is None:
            return self.db.query(ModelEvent).filter(
                ModelEvent.name.ilike(f'%HackEPS {str(year-1)}%')).first()
        return e

    def get_hacker_group(self, event_id: int, hacker_id: int, data: BaseToken):
        event = self.get_by_id(event_id)
        hacker = self.hacker_service.get_by_id(hacker_id)
        if hacker not in event.registered_hackers:
            raise NotFoundException("Hacker is not participant")
        user_groups = self.db.query(ModelHackerGroupUser).filter(
            ModelHackerGroupUser.hacker_id == hacker_id).all()
        group = self.db.query(ModelHackerGroup).filter(
            ModelHackerGroup.event_id == event_id).filter(
                ModelHackerGroup.id.in_(
                    [g.hacker_group_id for g in user_groups])).first()
        return group

    
    
    def get_event(self, id: int, data: BaseToken):
        event = self.get_by_id(id)
        if not data.check([UserType.LLEIDAHACKER]):
            return parse_obj_as(EventGetAllSchema, event)
        return parse_obj_as(EventGetSchema, event)

    def add_event(self, payload: EventCreateSchema, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER, UserType.SERVICE]):
            raise AuthenticationException("Not authorized")
        if payload.image is not None:
            payload = check_image(payload)
        db_event = ModelEvent(**payload.dict())
        self.db.add(db_event)
        self.db.commit()
        self.db.refresh(db_event)
        return db_event

    def update_event(self, id: int, event: EventUpdateSchema, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        db_event = self.get_by_id(id)
        if event.image is not None:
            event = check_image(event)
        updated = set_existing_data(db_event, event)
        self.db.commit()
        return db_event, updated

    def delete_event(self, id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER.value]):
            raise AuthenticationException("Not authorized")
        db_event = self.get_by_id(id)
        self.db.delete(db_event)
        self.db.commit()
        return db_event

    def is_registered(self, id: int, hacker_id: int, data: BaseToken):
        event = self.get_by_id(id)
        hacker = self.hacker_service.get_by_id(hacker_id)
        return hacker in event.registered_hackers

    def is_accepted(self, id: int, hacker_id: int, data: BaseToken):
        event = self.get_by_id(id)
        hacker = self.hacker_service.get_by_id(hacker_id)
        return hacker in event.accepted_hackers

    def get_event_meals(self, id: int, data: BaseToken):
        event = self.get_by_id(id)
        return event.meals

    def get_event_participants(self, id: int, data: BaseToken):
        event = self.get_by_id(id)
        return event.registered_hackers

    def get_event_sponsors(self, id: int):
        event = self.get_by_id(id)
        return event.sponsors

    def get_event_groups(self, id: int, data: BaseToken):
        event = self.get_by_id(id)
        return event

    def add_company(self, id: int, company_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(id)
        company = self.company_service.get_by_id(company_id)
        event.sponsors.append(company)
        self.db.commit()
        self.db.refresh(event)
        self.db.refresh(company)
        return event

    # def add_hacker(id: int, hacker_id: int, db: Session, data: BaseToken):
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

    def add_hacker_group(self, id: int, hacker_group_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER, UserType.HACKER]):
            raise AuthenticationException("Not authorized")
        hacker_group = self.db.query(ModelHackerGroup).filter(
            ModelHackerGroup.id == hacker_group_id).first()
        grou_hackers = [hacker.id for hacker in hacker_group.hackers]
        if not data.is_admin and (data.user_id not in grou_hackers or hacker_group.leader_id != data.user_id):
            raise AuthenticationException("Not authorized")
        if hacker_group is None:
            raise AuthenticationException("Hacker group not found")
        event = self.db.query(ModelEvent).filter(ModelEvent.id == id).first()
        if event is None:
            raise Exception("Event not found")
        if not data.is_admin and (event.max_participants <= len(event.hackers) + len(hacker_group.hackers)):
            raise Exception("Event is full")
        event.hacker_groups.append(hacker_group)
        event.hackers.extend(hacker_group.hackers)
        self.db.commit()
        self.db.refresh(event)
        return event

    def remove_company(self, id: int, company_id: int, data: BaseToken):
        if not data.chek([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        company = self.db.query(ModelCompany).filter(
            ModelCompany.id == company_id).first()
        if company is None:
            raise NotFoundException("Company not found")
        company_users = [user.id for user in company.users]
        if not data.is_admin or data.user_id not in company_users:
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

        # def remove_hacker(id: int, hacker_id: int, db: Session, data: BaseToken):
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
                            data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER, UserType.HACKER.value]):
            raise Exception("Not authorized")
        hacker_group = self.db.query(ModelHackerGroup).filter(
            ModelHackerGroup.id == hacker_group_id).first()
        if hacker_group is None:
            raise Exception("Hacker group not found")
        group_hackers = [hacker.id for hacker in hacker_group.members]
        if not data.is_admin or data.user_id not in group_hackers or hacker_group.leader_id != data.user_id:
            raise Exception("Not authorized")
        event = self.get_by_id(id)
        event.hacker_groups.remove(hacker_group)
        for hacker in hacker_group.members:
            event.registered_hackers.remove(hacker)
        self.db.commit()
        self.db.refresh(hacker_group)
        self.db.refresh(event)
        return event

    def get_accepted_hackers(self, event_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(event_id)
        return parse_obj_as(HackerGetAllSchema, event.accepted_hackers)

    def get_accepted_hackers_mails(self, event_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(event_id)
        hackers = [h.email for h in event.accepted_hackers]
        return parse_obj_as(HackerGetAllSchema, hackers)

    def get_sizes(self, eventId: int):
        sizes = {}
        event= self.get_by_id(eventId)
        for user in event.registered_hackers:
            if user.shirt_size is not None and user.shirt_size.strip() != "":
                if user.shirt_size in sizes:
                    sizes[user.shirt_size] += 1
                else:
                    sizes[user.shirt_size] = 1
        return sizes


    def get_accepted_and_confirmed(self, eventId: int):
        event= self.get_by_id(eventId)
        accepted_and_confirmed = []
        for user in event.accepted_hackers:
            user_registration = self.query(ModelHackerRegistration).filter(
                ModelHackerRegistration.user_id == user.id,
                ModelHackerRegistration.event_id == event.id).first()
            if user_registration and user_registration.confirmed_assistance:
                accepted_and_confirmed.append(user)
        return accepted_and_confirmed


    def get_hackers_unregistered(self, eventId: int):
        hackers = self.hacker_service.get_all()
        event = self.get_by_id(eventId)
        return subtract_lists(hackers, event.registered_hackers)


    def count_hackers_unregistered(self, eventId: int):
        return len(self.get_hackers_unregistered(eventId))

    def get_event_status(self, eventId: int):
        event = self.get_by_id(eventId)
        data = {
            'registratedUsers': len(event.registered_hackers),
            'groups': len(event.groups),
            'acceptedUsers': len(event.accepted_hackers),
            'rejectedUsers': len(event.rejected_hackers),
            'participatingUsers': len(event.participants),
            'acceptedAndConfirmedUsers': len(self.get_accepted_and_confirmed(eventId)),
        }
        for meal in event.meals:
            data[meal.name] = len(meal.users)
        return data


    def get_food_restrictions(self, eventId: int):
        event = self.get_by_id(eventId)
        users = event.participants + event.accepted_hackers + event.registered_hackers
        restrictions = []
        for user in users:
            if user.food_restrictions is not None and user.food_restrictions.strip(
            ) != "" and user.food_restrictions.strip() != 'no':
                restrictions.append(user.food_restrictions)
        # remove duplicates
        return list(set(restrictions))
    
    def get_pending_hackers_gruped(self, event: ModelEvent, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        # Extract hacker IDs from registered_hackers
        pending_hackers_ids = [
            h.id for h in subtract_lists(event.registered_hackers,
                                        event.accepted_hackers)
        ]
        # Retrieve pending hacker groups
        pending_groups_ids = self.db.query(ModelHackerGroupUser.group_id).filter(
            ModelHackerGroupUser.hacker_id.in_(pending_hackers_ids)).all()
        pending_groups_ids = [g[0] for g in pending_groups_ids]
        #remove duplicates
        pending_groups_ids = list(dict.fromkeys(pending_groups_ids))
        pending_groups = self.db.query(ModelHackerGroup).filter(
            ModelHackerGroup.id.in_(pending_groups_ids)).all()
        # return pending_groups_ids
        # Collect group users' IDs
        group_users = [
            hacker.id for group in pending_groups for hacker in group.members
        ]
        # Prepare the output data
        output_data = []
        for group in pending_groups:
            group_data = {
                "name":
                group.name,
                "members": [{
                    "id": hacker.id,
                    "name": hacker.name,
                    "birthdate": hacker.birthdate,
                    "address": hacker.address,
                    "food_restrictions": hacker.food_restrictions,
                    "shirt_size": hacker.shirt_size,
                    "approved": hacker in event.accepted_hackers,
                } for hacker in group.members]
            }
            output_data.append(group_data)
        # Handle hackers without a group
        nogroup_data = [{
            "id": hacker.id,
            "name": hacker.name,
            "birthdate": hacker.birthdate,
            "address": hacker.address,
            "food_restrictions": hacker.food_restrictions,
            "shirt_size": hacker.shirt_size,
            "approved": hacker in event.accepted_hackers,
        } for hacker in subtract_lists(event.registered_hackers,
                                    event.accepted_hackers)
                        if hacker.id not in group_users]

        # Combine group and nogroup data into a dictionary
        return {"groups": output_data, "nogroup": nogroup_data}