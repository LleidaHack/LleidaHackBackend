from fastapi_sqlalchemy import db

# from src.impl.HackerGroup.service import HackerGroupService
from services.mail import send_event_accepted_email
from src.error.AuthenticationException import AuthenticationException
from src.error.InvalidDataException import InvalidDataException
from src.error.NotFoundException import NotFoundException
from src.impl.Company.service import CompanyService
from src.impl.Event.model import Event as ModelEvent
from src.impl.Event.model import HackerRegistration as ModelHackerRegistration
from src.impl.Event.schema import EventCreate as EventCreateSchema
from src.impl.Event.schema import EventGet as EventGetSchema
from src.impl.Event.schema import EventGetAll as EventGetAllSchema
from src.impl.Event.schema import EventUpdate as EventUpdateSchema
from src.impl.Hacker.schema import HackerGetAll as HackerGetAllSchema
from src.impl.Hacker.service import HackerService
from src.impl.HackerGroup.model import HackerGroup as ModelHackerGroup
from src.impl.HackerGroup.model import HackerGroupUser as ModelHackerGroupUser
from src.utils.Base.BaseService import BaseService
from src.utils.service_utils import (check_image, set_existing_data,
                                     subtract_lists)
from src.utils.Token import AssistenceToken, BaseToken
from src.utils.UserType import UserType


class EventService(BaseService):
    name = 'event_service'
    hackergroup_service = None
    hacker_service = None
    company_service = None

    def get_all(self):
        return db.session.query(ModelEvent).filter(ModelEvent.archived == True).all()

    def get_archived(self):
        return db.session.query(ModelEvent).filter(ModelEvent.archived == False).all()
    
    def get_by_id(self, id: int) -> ModelEvent:
        event = db.session.query(ModelEvent).filter(
            ModelEvent.id == id).first()
        if event is None:
            raise NotFoundException('event not found')
        return event
    
    def get_hackeps(self, year: int):
        #return and event called HackEPS year ignoring caps
        e = db.session.query(ModelEvent).filter(
            ModelEvent.name.ilike(f'%HackEPS {str(year)}%')).first()
        if e is None:
            return db.session.query(ModelEvent).filter(
                ModelEvent.name.ilike(f'%HackEPS {str(year-1)}%')).first()
        return e
    def archive(self, id:int, data:BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(id)
        if event.archived:
            raise InvalidDataException("Event is already archived")
        event.archived = True
        db.session.commit()
        db.session.refresh(event)
        return event
    
    def unarchive(self, id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(id)
        if not event.archived:
            raise InvalidDataException("Event is not archived")
        event.archived = False
        db.session.commit()
        db.session.refresh(event)
        return event
    
    @BaseService.needs_service(HackerService)
    def get_hacker_group(self, event_id: int, hacker_id: int, data: BaseToken):
        event = self.get_by_id(event_id)
        hacker = self.hacker_service.get_by_id(hacker_id)
        if hacker not in event.registered_hackers:
            raise NotFoundException("Hacker is not participant")
        user_groups = db.session.query(ModelHackerGroupUser).filter(
            ModelHackerGroupUser.hacker_id == hacker_id).all()
        group = db.session.query(ModelHackerGroup).filter(
            ModelHackerGroup.event_id == event_id).filter(
                ModelHackerGroup.id.in_(
                    [g.hacker_group_id for g in user_groups])).first()
        return group

    def get_event(self, id: int, data: BaseToken):
        event = self.get_by_id(id)
        if not data.check([UserType.LLEIDAHACKER]):
            return EventGetAllSchema.from_orm(event)
        return EventGetSchema.from_orm(event)

    def add_event(self, payload: EventCreateSchema, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER, UserType.SERVICE]):
            raise AuthenticationException("Not authorized")
        if payload.image is not None:
            payload = check_image(payload)
        db_event = ModelEvent(**payload.dict())
        db.session.add(db_event)
        db.session.commit()
        db.session.refresh(db_event)
        return db_event

    def update_event(self, id: int, event: EventUpdateSchema, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        db_event = self.get_by_id(id)
        if event.archived:
            raise InvalidDataException("Unable to update an archived event, unarchive it first")
        if event.image is not None:
            event = check_image(event)
        updated = set_existing_data(db_event, event)
        db.session.commit()
        return db_event, updated

    def delete_event(self, id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        db_event = self.get_by_id(id)
        # if db_event.archived:
        #     raise InvalidDataException("Unable to delete an archived event, unarchive it first")
        db.session.delete(db_event)
        db.session.commit()
        return db_event

    @BaseService.needs_service(HackerService)
    def is_registered(self, id: int, hacker_id: int, data: BaseToken):
        event = self.get_by_id(id)
        hacker = self.hacker_service.get_by_id(hacker_id)
        return hacker in event.registered_hackers

    @BaseService.needs_service(HackerService)
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
        return event.groups

    @BaseService.needs_service(CompanyService)
    def add_company(self, id: int, company_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(id)
        if event.archived:
            raise InvalidDataException("Unable to operate with an archived event, unarchive it first")
        company = self.company_service.get_by_id(company_id)
        event.sponsors.append(company)
        db.session.commit()
        db.session.refresh(event)
        db.session.refresh(company)
        return event

    @BaseService.needs_service(HackerService)
    def add_hacker(self, event_id: int, hacker_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]) or not data.check([UserType.HACKER], hacker_id):
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(event_id)
        if event.archived:
            raise InvalidDataException("Unable to operate with an archived event, unarchive it first")
        if not data.is_admin:
            if event.max_participants <= len(event.registered_hackers):
                raise Exception("Event is full")
        hacker = self.hacker_service.get_by_id(hacker_id)
        event.registered_hackers.append(hacker)
        db.session.commit()
        db.session.refresh(event)
        db.session.refresh(hacker)
        return event

    @BaseService.needs_service('HackerGroupService')
    def add_hacker_group(self, id: int, hacker_group_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER, UserType.HACKER]):
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(id)
        if event.archived:
            raise InvalidDataException("Unable to operate with an archived event, unarchive it first")
        hacker_group = self.hackergroup_service.get_by_id(hacker_group_id)
        grou_hackers = [hacker.id for hacker in hacker_group.hackers]
        if not data.is_admin and (data.user_id not in grou_hackers
                                  or hacker_group.leader_id != data.user_id):
            raise AuthenticationException("Not authorized")
        if hacker_group is None:
            raise AuthenticationException("Hacker group not found")
        if event.max_participants <= (len(event.hackers) +
                                      len(hacker_group.hackers)):
            raise InvalidDataException("Event is full")
        event.hacker_groups.append(hacker_group)
        event.hackers.extend(hacker_group.hackers)
        db.session.commit()
        db.session.refresh(event)
        return event

    @BaseService.needs_service(CompanyService)
    def remove_company(self, id: int, company_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(id)
        if event.archived:
            raise InvalidDataException("Unable to operate with an archived event, unarchive it first")
        company = self.company_service.get_by_id(company_id)
        company_users = [user.id for user in company.users]
        if not data.is_admin or data.user_id not in company_users:
            raise AuthenticationException("Not authorized")
        if company not in event.companies:
            raise InvalidDataException("Company is not sponsor")
        event.companies.remove(company)
        db.session.commit()
        db.session.refresh(event)
        db.session.refresh(company)
        return event

    @BaseService.needs_service('HackerGroupService')
    def remove_hacker_group(self, id: int, hacker_group_id: int,
                            data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER, UserType.HACKER]):
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(id)
        if event.archived:
            raise InvalidDataException("Unable to operate with an archived event, unarchive it first")
        hacker_group = self.hackergroup_service.get_by_id(hacker_group_id)
        group_hackers = [hacker.id for hacker in hacker_group.members]
        if not data.is_admin or data.user_id not in group_hackers or hacker_group.leader_id != data.user_id:
            raise AuthenticationException("Not authorized")
        event.hacker_groups.remove(hacker_group)
        for hacker in hacker_group.members:
            event.registered_hackers.remove(hacker)
        db.session.commit()
        db.session.refresh(hacker_group)
        db.session.refresh(event)
        return event

    def get_accepted_hackers(self, event_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(event_id)
        return HackerGetAllSchema.from_orm(event.accepted_hackers)

    def get_accepted_hackers_mails(self, event_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(event_id)
        hackers = [h.email for h in event.accepted_hackers]
        return hackers

    def get_sizes(self, eventId: int):
        sizes = {}
        event = self.get_by_id(eventId)
        for user in event.registered_hackers:
            if user.shirt_size is not None and user.shirt_size.strip() != "":
                if user.shirt_size in sizes:
                    sizes[user.shirt_size] += 1
                else:
                    sizes[user.shirt_size] = 1
        return sizes

    def get_accepted_and_confirmed(self, eventId: int):
        event = self.get_by_id(eventId)
        accepted_and_confirmed = []
        for user in event.accepted_hackers:
            user_registration = db.session.query(
                ModelHackerRegistration).filter(
                    ModelHackerRegistration.user_id == user.id,
                    ModelHackerRegistration.event_id == event.id).first()
            if user_registration and user_registration.confirmed_assistance:
                accepted_and_confirmed.append(user)
        return accepted_and_confirmed

    @BaseService.needs_service('HackerGroupService')
    def get_hackers_unregistered(self, eventId: int):
        hackers = self.hacker_service.get_all()
        event = self.get_by_id(eventId)
        return subtract_lists(hackers, event.registered_hackers)

    def count_hackers_unregistered(self, eventId: int):
        return len(self.get_hackers_unregistered(eventId))

    def get_status(self, eventId: int):
        event = self.get_by_id(eventId)
        data = {
            'archived':
            event.archived,
            'is_open':
            event.is_open,
            'registratedUsers':
            len(event.registered_hackers),
            'groups':
            len(event.groups),
            'acceptedUsers':
            len(event.accepted_hackers),
            'rejectedUsers':
            len(event.rejected_hackers),
            'participatingUsers':
            len(event.participants),
            'acceptedAndConfirmedUsers':
            len(self.get_accepted_and_confirmed(eventId)),
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

    @BaseService.needs_service('HackerGroupService')
    def get_pending_hackers_gruped(self, event_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        # Extract hacker IDs from registered_hackers
        event = self.get_by_id(event_id)
        pending_hackers_ids = [
            h.id for h in subtract_lists(event.registered_hackers,
                                         event.accepted_hackers)
        ]
        # Retrieve pending hacker groups
        pending_groups_ids = db.session.query(
            ModelHackerGroupUser.group_id).filter(
                ModelHackerGroupUser.hacker_id.in_(pending_hackers_ids)).all()
        pending_groups_ids = [g[0] for g in pending_groups_ids]
        #remove duplicates
        pending_groups_ids = list(dict.fromkeys(pending_groups_ids))
        pending_groups = self.hackergroup_service.get_when_id_in(
            pending_groups_ids)
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

    @BaseService.needs_service(HackerService)
    def confirm_assistance(self, data: AssistenceToken):
        # data = get_data_from_token(token, special=True)
        # if data.expt < datetime.utcnow().isoformat():
        event = self.get_by_id(data.event_id)
        if event.archived:
            raise InvalidDataException("Unable to operate with an archived event, unarchive it first")
        user = self.hacker_service.get_by_id(data.user_id)
        user_registration = db.session.query(ModelHackerRegistration).filter(
            ModelHackerRegistration.user_id == data.user_id,
            ModelHackerRegistration.event_id == data.event_id).first()
        if user_registration is None:
            raise InvalidDataException("User not registered")
        if user_registration.confirm_assistance_token != data.to_token():
            raise InvalidDataException("Invalid token")
        if user not in event.accepted_hackers:
            raise InvalidDataException("User not accepted")
        if user_registration.confirmed_assistance:
            raise InvalidDataException("User already confirmed assistance")
        user_registration.confirmed_assistance = True
        db.session.commit()
        db.session.refresh(user_registration)
        return user_registration

    @BaseService.needs_service(HackerService)
    def force_confirm_assistance(self, user_id: int, event_id: int,
                                 data: BaseToken):
        if not data.is_admin:
            raise AuthenticationException(
                "You don't have permissions to do this")
        user = self.hacker_service.get_by_id(user_id)
        event = self.get_by_id(event_id)
        user_registration = db.session.query(ModelHackerRegistration).filter(
            ModelHackerRegistration.user_id == user_id,
            ModelHackerRegistration.event_id == event_id).first()
        if user_registration is None:
            raise InvalidDataException("User not registered")
        if user not in event.accepted_hackers:
            raise InvalidDataException("User not accepted")
        if user_registration.confirmed_assistance:
            raise InvalidDataException("User already confirmed assistance")
        user_registration.confirmed_assistance = True
        db.session.commit()
        db.session.refresh(user_registration)
        return user_registration

    @BaseService.needs_service(HackerService)
    def participate_hacker(self, event_id: int, hacker_code: str,
                           data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(event_id)
        if event.archived:
            raise InvalidDataException("Unable to operate with an archived event, unarchive it first")
        hacker = self.hacker_service.get_by_code(hacker_code)
        message = ''
        if hacker in event.participants:
            raise InvalidDataException("Hacker already participating")
        if not hacker in event.accepted_hackers:
            raise InvalidDataException("Hacker not accepted")
        user_registration = db.session.query(ModelHackerRegistration).filter(
            ModelHackerRegistration.user_id == hacker.user_id,
            ModelHackerRegistration.event_id == event.id).first()
        if user_registration is None:
            raise InvalidDataException("User not registered")
        if not user_registration.confirmed_assistance:
            user_registration.confirmed_assistance = True
            message = "user haven't confirmed so we frced confirmation"
            # raise InvalidDataException("User not confirmed assitence")
        event.participants.append(hacker)
        db.session.commit()
        db.session.refresh(user_registration)
        db.session.refresh(event)
        db.session.refresh(hacker)
        return {
            'success': True,
            'event_id': event.id,
            'hacker_id': hacker.id,
            'hacker_name': hacker.name,
            'hacker_shirt_size': user_registration.shirt_size,
            'food_restrictions': user_registration.food_restrictions,
            'message': message,
        }

    @BaseService.needs_service(HackerService)
    def unparticipate_hacker(self, event_id: int, hacker_code: str,
                             data: BaseToken):
        if not data.is_admin:
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(event_id)
        if event.archived:
            raise InvalidDataException("Unable to operate with an archived event, unarchive it first")
        hacker = self.hacker_service.get_by_code(hacker_code)
        if not hacker in event.participants:
            raise InvalidDataException("Hacker not participating")
        event.participants.remove(hacker)
        db.session.commit()
        db.session.refresh(event)
        db.session.refresh(hacker)
        return event

    @BaseService.needs_service(HackerService)
    def accept_hacker(self, event_id: int, hacker_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(event_id)
        if event.archived:
            raise InvalidDataException("Unable to operate with an archived event, unarchive it first")
        hacker = self.hacker_service.get_by_id(hacker_id)
        if not hacker in event.registered_hackers:
            raise InvalidDataException("Hacker not registered")
        if hacker in event.accepted_hackers:
            raise InvalidDataException("Hacker already accepted")
        hacker_registration = db.session.query(ModelHackerRegistration).filter(
            ModelHackerRegistration.user_id == hacker.id,
            ModelHackerRegistration.event_id == event.id).first()
        if hacker_registration is None:
            raise InvalidDataException("Hacker not registered")
        token = AssistenceToken(hacker, event.id).to_token()
        hacker_registration.confirm_assistance_token = token
        event.accepted_hackers.append(hacker)
        db.session.commit()
        db.session.refresh(event)
        db.session.refresh(hacker)
        # send_event_accepted_email(hacker, event, token)
        return event

    @BaseService.needs_service(HackerService)
    def unaccept_hacker(self, event_id: int, hacker_id: int, data: BaseToken):
        if not data.is_admin:
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(event_id)
        if event.archived:
            raise InvalidDataException("Unable to operate with an archived event, unarchive it first")
        hacker = self.hacker_service.get_by_id(hacker_id)
        if not hacker in event.accepted_hackers:
            raise InvalidDataException("Hacker not accepted")
        event.accepted_hackers.remove(hacker)
        db.session.commit()
        db.session.refresh(event)
        db.session.refresh(hacker)
        return event

    @BaseService.needs_service('HackerGroupService')
    def reject_group(self, event_id: int, group_id, data: BaseToken):
        if not data.is_admin:
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(event_id)
        if event.archived:
            raise InvalidDataException("Unable to operate with an archived event, unarchive it first")
        group = self.hackergroup_service.get_by_id(group_id)
        for hacker in group.members and hacker not in event.accepted_hackers:
            if hacker not in event.registered_hackers:
                raise InvalidDataException("Hacker not registered")
            if hacker in event.accepted_hackers:
                raise InvalidDataException("Hacker already accepted")
            event.rejected_hackers.append(hacker)
        db.session.commit()
        db.session.refresh(event)
        db.session.refresh(group)
        return event

    @BaseService.needs_service(HackerService)
    def reject_hacker(self, event_id: int, hacker_id: int, data: BaseToken):
        if not data.is_admin:
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(event_id)
        if event.archived:
            raise InvalidDataException("Unable to operate with an archived event, unarchive it first")
        hacker = self.hacker_service.get_by_id(hacker_id)
        if not hacker in event.registered_hackers:
            raise InvalidDataException("Hacker not registered")
        if hacker in event.accepted_hackers:
            raise InvalidDataException("Hacker already accepted")
        event.rejected_hackers.remove(hacker)
        db.session.commit()
        db.session.refresh(event)
        db.session.refresh(hacker)
        return event

    @BaseService.needs_service('HackerGroupService')
    def accept_group(self, event_id: int, group_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(event_id)
        if event.archived:
            raise InvalidDataException("Unable to operate with an archived event, unarchive it first")
        group = self.hackergroup_service.get_by_id(group_id)
        for hacker in subtract_lists(group.members, event.accepted_hackers):
            if hacker not in event.registered_hackers:
                raise InvalidDataException("Hacker not registered")
            hacker_user = self.hacker_service.get_by_id(hacker.id)
            self.accept_hacker(event.id, hacker_user.id, data)

    