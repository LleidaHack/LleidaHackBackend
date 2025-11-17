from fastapi_sqlalchemy import db
from sqlalchemy import desc
from datetime import datetime
from generated_src.lleida_hack_mail_api_client.models.mail_create import MailCreate
from collections import Counter

# from src.impl.HackerGroup.service import HackerGroupService
# from services.mail import send_event_accepted_email
from src.error.AuthenticationException import AuthenticationException
from src.error.InvalidDataException import InvalidDataException
from src.error.NotFoundException import NotFoundException
from src.impl.Company.service import CompanyService
from src.impl.Event.model import Event
from src.impl.Event.model import HackerRegistration
from src.impl.Event.schema import EventCreate
from src.impl.Event.schema import HackerEventRegistration
from src.impl.Event.schema import EventGet
from src.impl.Event.schema import EventGetAll
from src.impl.Event.schema import EventUpdate
from src.impl.Hacker.service import HackerService
from src.impl.HackerGroup.model import HackerGroup
from src.impl.HackerGroup.model import HackerGroupUser
from src.impl.Mail.client import MailClient
from src.impl.Mail.internall_templates import InternalTemplate
from src.utils.Base.BaseClient import BaseClient
from src.utils.Base.BaseService import BaseService
from src.utils.service_utils import (
    check_image,
    set_existing_data,
    subtract_lists,
    get_hacker_info,
)
from src.utils.Token import AssistenceToken, BaseToken
from src.utils.UserType import UserType


class EventService(BaseService):
    name = "event_service"
    hackergroup_service = None
    hacker_service: HackerService = None
    company_service: CompanyService = None
    mail_client: MailClient = None

    def get_all(self):
        return db.session.query(Event).filter(Event.archived.is_(False)).all()

    def get_archived(self):
        return db.session.query(Event).filter(Event.archived.is_(True)).all()

    def get_by_id(self, id: int) -> Event:
        event = db.session.query(Event).filter(Event.id == id).first()
        if event is None:
            raise NotFoundException("event not found")
        return event

    def get_hackeps(self, year: int):
        # return and event called HackEPS year ignoring caps
        e = (
            db.session.query(Event)
            .filter(
                Event.name.ilike("HackEPS%"), Event.start_date <= datetime(year, 12, 31)
            )
            .order_by(desc(Event.end_date))
            .first()
        )
        if e is None:
            raise NotFoundException("We can't find an event for this year or earlier ")

        return e

    def archive(self, id: int, data: BaseToken):
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
        user_groups = (
            db.session.query(HackerGroupUser)
            .filter(HackerGroupUser.hacker_id == hacker_id)
            .all()
        )
        group = (
            db.session.query(HackerGroup)
            .filter(HackerGroup.event_id == event_id)
            .filter(HackerGroup.id.in_([g.hacker_group_id for g in user_groups]))
            .first()
        )
        return group

    def get_event(self, id: int, data: BaseToken):
        event = self.get_by_id(id)
        if not data.check([UserType.LLEIDAHACKER]):
            return EventGetAll.model_validate(event)
        return EventGet.model_validate(event)

    def add_event(self, payload: EventCreate, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER, UserType.SERVICE]):
            raise AuthenticationException("Not authorized")
        if payload.image is not None:
            payload = check_image(payload)
        db_event = Event(**payload.model_dump())
        db.session.add(db_event)
        db.session.commit()
        db.session.refresh(db_event)
        return db_event

    def update_event(self, id: int, event: EventUpdate, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        db_event = self.get_by_id(id)
        if event.archived:
            raise InvalidDataException(
                "Unable to update an archived event, unarchive it first"
            )
        if event.image is not None:
            event = check_image(event)
        updated = set_existing_data(db_event, event)
        db.session.commit()
        return db_event, updated

    def delete_event(self, id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        db_event = self.get_by_id(id)
        if db_event.archived:
            raise InvalidDataException(
                "Unable to delete an archived event, unarchive it first"
            )
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

    def has_confirmed(self, id: int, hacker_id: int, data: BaseToken):
        user_registration = (
            db.session.query(HackerRegistration)
            .filter(
                HackerRegistration.user_id == hacker_id,
                HackerRegistration.event_id == id,
            )
            .first()
        )
        return user_registration.confirmed_assistance

    @BaseService.needs_service(HackerService)
    def is_participant(self, id: int, hacker_id: int, data: BaseToken):
        event = self.get_by_id(id)
        hacker = self.hacker_service.get_by_id(hacker_id)
        return hacker in event.participants

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
            raise InvalidDataException(
                "Unable to operate with an archived event, unarchive it first"
            )
        company = self.company_service.get_by_id(company_id)
        event.sponsors.append(company)
        db.session.commit()
        db.session.refresh(event)
        db.session.refresh(company)
        return event

    @BaseClient.needs_client(MailClient)
    @BaseService.needs_service(HackerService)
    def add_hacker(
        self,
        event_id: int,
        hacker_id: int,
        payload: HackerEventRegistration,
        data: BaseToken,
    ):
        if not data.check([UserType.LLEIDAHACKER]) and not data.check(
            [UserType.HACKER], hacker_id
        ):
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(event_id)
        if event.archived:
            raise InvalidDataException(
                "Unable to operate with an archived event, unarchive it first"
            )
        if not event.is_open:
            raise InvalidDataException(
                "Unable to operate with a closed event, reopen it first"
            )
        if not data.is_admin:
            if event.max_participants <= len(event.accepted_hackers):
                raise InvalidDataException("Event is full")
        hacker = self.hacker_service.get_by_id(hacker_id)
        if hacker in event.registered_hackers:
            raise InvalidDataException("Hacker already registered")
        reg = HackerRegistration(
            **payload.model_dump(), user_id=hacker_id, event_id=event_id
        )
        if payload.update_user:
            set_existing_data(hacker, payload)
            hacker.address = payload.location
        mail = self.mail_client.create_mail(
            MailCreate(
                template_id=self.mail_client.get_internall_template_id(
                    InternalTemplate.EVENT_HACKER_REGISTERED
                ),
                receiver_id=str(hacker.id),
                receiver_mail=str(hacker.email),
                subject=f"Your have registered to {event.name}",
                fields=f"{hacker.name}",
            )
        )
        self.mail_client.send_mail_by_id(mail.id)
        db.session.add(reg)
        db.session.commit()
        db.session.refresh(event)
        db.session.refresh(hacker)
        return event

    @BaseService.needs_service(HackerService)
    def update_register(
        self,
        event_id: int,
        hacker_id: int,
        payload: HackerEventRegistration,
        data: BaseToken,
    ):
        if not data.check([UserType.LLEIDAHACKER]) and not data.check(
            [UserType.HACKER], hacker_id
        ):
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(event_id)
        if event.archived:
            raise InvalidDataException(
                "Unable to operate with an archived event, unarchive it first"
            )
        if not data.is_admin:
            if event.max_participants <= len(event.registered_hackers):
                raise InvalidDataException("Event is full")
        hacker = self.hacker_service.get_by_id(hacker_id)
        if hacker not in event.registered_hackers:
            raise InvalidDataException("Hacker is not registered")
        reg = (
            db.session.query(HackerEventRegistration)
            .filter(
                HackerRegistration.user_id == hacker_id,
                HackerRegistration.event_id == event_id,
            )
            .first()
        )
        if reg is None:
            raise InvalidDataException("Hacker is not registered")
        set_existing_data(reg, payload)
        if payload.update_user:
            set_existing_data(hacker, payload)
            hacker.address = payload.location
        db.session.commit()
        db.session.refresh(event)
        db.session.refresh(hacker)
        return event

    @BaseService.needs_service("HackerGroupService")
    def add_hacker_group(self, id: int, hacker_group_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER, UserType.HACKER]):
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(id)
        if event.archived:
            raise InvalidDataException(
                "Unable to operate with an archived event, unarchive it first"
            )
        hacker_group = self.hackergroup_service.get_by_id(hacker_group_id)
        grou_hackers = [hacker.id for hacker in hacker_group.hackers]
        if not data.is_admin and (
            data.user_id not in grou_hackers or hacker_group.leader_id != data.user_id
        ):
            raise AuthenticationException("Not authorized")
        if hacker_group is None:
            raise AuthenticationException("Hacker group not found")
        if event.max_participants <= (len(event.hackers) + len(hacker_group.hackers)):
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
            raise InvalidDataException(
                "Unable to operate with an archived event, unarchive it first"
            )
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

    @BaseService.needs_service("HackerGroupService")
    def remove_hacker_group(self, id: int, hacker_group_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER, UserType.HACKER]):
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(id)
        if event.archived:
            raise InvalidDataException(
                "Unable to operate with an archived event, unarchive it first"
            )
        hacker_group = self.hackergroup_service.get_by_id(hacker_group_id)
        group_hackers = [hacker.id for hacker in hacker_group.members]
        if (
            not data.is_admin
            or data.user_id not in group_hackers
            or hacker_group.leader_id != data.user_id
        ):
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
        return event.accepted_hackers

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
            user_registration = (
                db.session.query(HackerRegistration)
                .filter(
                    HackerRegistration.user_id == user.id,
                    HackerRegistration.event_id == event.id,
                )
                .first()
            )
            if user_registration and user_registration.confirmed_assistance:
                accepted_and_confirmed.append(user)
        return accepted_and_confirmed

    @BaseService.needs_service("HackerGroupService")
    def get_hackers_unregistered(self, eventId: int):
        hackers = self.hacker_service.get_all()
        event = self.get_by_id(eventId)
        return subtract_lists(hackers, event.registered_hackers)

    def count_hackers_unregistered(self, eventId: int):
        return len(self.get_hackers_unregistered(eventId))

    def get_status(self, eventId: int):
        event = self.get_by_id(eventId)
        data = {
            "archived": event.archived,
            "is_open": event.is_open,
            "registratedUsers": len(event.registered_hackers),
            "groups": len(event.groups),
            "acceptedUsers": len(event.accepted_hackers),
            "rejectedUsers": len(event.rejected_hackers),
            "participatingUsers": len(event.participants),
            "acceptedAndConfirmedUsers": len(self.get_accepted_and_confirmed(eventId)),
        }
        for meal in event.meals:
            data[meal.name] = len(meal.users)
        return data

    def get_statistics(self, eventId: int):
        event = self.get_by_id(eventId)
        data = {
            "how_did_you_meet_us": [],
            "location": [],
            "study_center": [],
            "studies": [],
        }
        for hacker in event.accepted_hackers:
            data["how_did_you_meet_us"].append(hacker.how_did_you_meet_us)
            data["location"].append(hacker.location)
            data["study_center"].append(hacker.study_center)
            data["studies"].append(hacker.studies)
        data["how_did_you_meet_us"] = dict(Counter(data["how_did_you_meet_us"]))
        return data

    def get_food_restrictions(self, eventId: int):
        event = self.get_by_id(eventId)
        users = event.participants + event.accepted_hackers + event.registered_hackers
        restrictions = []
        for user in users:
            if (
                user.food_restrictions is not None
                and user.food_restrictions.strip() != ""
                and user.food_restrictions.strip() != "no"
            ):
                restrictions.append(user.food_restrictions)
        # remove duplicates
        return list(set(restrictions))

    @BaseService.needs_service(HackerService)
    def get_credits(self, eventId: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        users = {_.id: _.email for _ in self.hacker_service.get_all()}
        regs = (
            db.session.query(HackerRegistration)
            .filter(
                HackerRegistration.event_id == eventId,
                HackerRegistration.wants_credit,
            )
            .all()
        )
        return [users[_.user_id] for _ in regs]

    @BaseService.needs_service("HackerGroupService")
    def get_pending_hackers_gruped(self, event_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        # Extract hacker IDs from registered_hackers
        event = self.get_by_id(event_id)
        pending_hackers_ids = [
            h.id
            for h in subtract_lists(event.registered_hackers, event.accepted_hackers)
        ]
        # Retrieve pending hacker groups

        pending_groups_ids = (
            db.session.query(HackerGroupUser.group_id)
            .filter(
                HackerGroupUser.hacker_id.in_(pending_hackers_ids),
                HackerGroupUser.group_id.in_([_.id for _ in event.groups]),
            )
            .all()
        )
        pending_groups_ids = [g[0] for g in pending_groups_ids]
        # remove duplicates
        pending_groups_ids = list(dict.fromkeys(pending_groups_ids))
        pending_groups = self.hackergroup_service.get_when_id_in(pending_groups_ids)
        # return pending_groups_ids
        # Collect group users' IDs
        group_users = [
            hacker.id
            for group in pending_groups
            for hacker in group.members
            if group.event_id == event_id
        ]
        # Prepare the output data
        output_data = []
        for group in pending_groups:
            group_data = {
                "name": group.name,
                "members": [
                    {
                        "id": hacker.id,
                        "name": hacker.name,
                        "email": hacker.email,
                        "birthdate": hacker.birthdate,
                        "address": hacker.address,
                        "food_restrictions": hacker.food_restrictions,
                        "shirt_size": hacker.shirt_size,
                        "approved": hacker in event.accepted_hackers,
                    }
                    for hacker in group.members
                ],
            }
            output_data.append(group_data)
        # Handle hackers without a group
        nogroup_data = [
            {
                "id": hacker.id,
                "name": hacker.name,
                "email": hacker.email,
                "birthdate": hacker.birthdate,
                "address": hacker.address,
                "food_restrictions": hacker.food_restrictions,
                "shirt_size": hacker.shirt_size,
                "approved": hacker in event.accepted_hackers,
            }
            for hacker in subtract_lists(
                event.registered_hackers, event.accepted_hackers
            )
            if hacker.id not in group_users
        ]

        # Combine group and nogroup data into a dictionary
        return {"groups": output_data, "nogroup": nogroup_data}

    @BaseService.needs_service("HackerGroupService")
    def get_hackers_participants_list(
        self, event_id: int, data: BaseToken
    ):  ##Servei per obtindre la llista de participants amb status acceptat, rechazat o pending.
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        # Extract hacker IDs from registered_hackers
        event = self.get_by_id(event_id)
        # Extract pending hackers
        pending_hackers_ids = [
            h.id
            for h in subtract_lists(
                subtract_lists(event.registered_hackers, event.accepted_hackers),
                event.rejected_hackers,
            )
        ]
        registered_hackers = event.registered_hackers
        # Accepted hackers
        accepted_hackers_ids = [h.id for h in event.accepted_hackers]
        # Rejected hackers
        rejected_hackers_ids = [h.id for h in event.rejected_hackers]

        # List hackers and add status as pending, accepted or rejected.
        participants_list = [
            get_hacker_info(
                hacker, pending_hackers_ids, accepted_hackers_ids, rejected_hackers_ids
            )
            for hacker in registered_hackers
        ]
        # Combine group and nogroup data into a dictionary
        return {"participants": participants_list}

    ## This returns 2 lists: people going alone and people in groups. They will have status and food restrictions.
    @BaseService.needs_service("HackerGroupService")
    def get_hackers_participants_grouped_list(self, event_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        # Extract hacker IDs from registered_hackers
        event = self.get_by_id(event_id)
        pending_hackers_ids = [
            h.id
            for h in subtract_lists(
                subtract_lists(event.registered_hackers, event.accepted_hackers),
                event.rejected_hackers,
            )
        ]
        # Registered hackers
        registered_hackers = event.registered_hackers
        # Accepted hackers
        accepted_hackers_ids = [h.id for h in event.accepted_hackers]
        # Rejected hackers
        rejected_hackers_ids = [h.id for h in event.rejected_hackers]

        event_groups = event.groups
        group_users = []
        for group in event_groups:
            group_users.extend([hacker.id for hacker in group.members])

        # List hackers and add status as pending, accepted or rejected.
        output_data = []
        non_group_hackers_ids = subtract_lists(
            pending_hackers_ids + accepted_hackers_ids + rejected_hackers_ids,
            group_users,
        )

        non_group_hackers_ids_set = set(non_group_hackers_ids)
        non_group_hackers = [
            hacker
            for hacker in registered_hackers
            if hacker.id in non_group_hackers_ids_set
        ]

        non_group_hackers_participants = [
            get_hacker_info(
                hacker, pending_hackers_ids, accepted_hackers_ids, rejected_hackers_ids
            )
            for hacker in non_group_hackers
        ]

        for group in event_groups:
            group_data = {
                "name": group.name,
                "members": [
                    get_hacker_info(
                        hacker,
                        pending_hackers_ids,
                        accepted_hackers_ids,
                        rejected_hackers_ids,
                    )
                    for hacker in group.members
                ],
            }
            output_data.append(group_data)
        # Retrieve pending hacker groups
        # Combine group and nogroup data into a dictionary
        return {"groups": output_data, "nogroup": non_group_hackers_participants}

    @BaseService.needs_service(HackerService)
    def confirm_assistance(self, data: AssistenceToken):
        # data = get_data_from_token(token, special=True)
        # if data.expt < datetime.now(UTC).isoformat():
        event = self.get_by_id(data.event_id)
        if event.archived:
            raise InvalidDataException(
                "Unable to operate with an archived event, unarchive it first"
            )
        user = self.hacker_service.get_by_id(data.user_id)
        user_registration = (
            db.session.query(HackerRegistration)
            .filter(
                HackerRegistration.user_id == data.user_id,
                HackerRegistration.event_id == data.event_id,
            )
            .first()
        )
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
    def force_confirm_assistance(self, user_id: int, event_id: int, data: BaseToken):
        if not data.is_admin:
            raise AuthenticationException("You don't have permissions to do this")
        user = self.hacker_service.get_by_id(user_id)
        event = self.get_by_id(event_id)
        user_registration = (
            db.session.query(HackerRegistration)
            .filter(
                HackerRegistration.user_id == user_id,
                HackerRegistration.event_id == event_id,
            )
            .first()
        )
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
    def participate_hacker(self, event_id: int, hacker_code: str, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(event_id)
        if event.archived:
            raise InvalidDataException(
                "Unable to operate with an archived event, unarchive it first"
            )
        hacker = self.hacker_service.get_by_code(hacker_code)
        message = ""
        if hacker in event.participants:
            raise InvalidDataException("Hacker already participating")
        if hacker not in event.accepted_hackers:
            raise InvalidDataException("Hacker not accepted")
        user_registration = (
            db.session.query(HackerRegistration)
            .filter(
                HackerRegistration.user_id == hacker.user_id,
                HackerRegistration.event_id == event.id,
            )
            .first()
        )
        if user_registration is None:
            raise InvalidDataException("User not registered")
        if not user_registration.confirmed_assistance:
            user_registration.confirmed_assistance = True
            message = "user haven't confirmed so we forced confirmation"
            # raise InvalidDataException("User not confirmed assitence")
        event.participants.append(hacker)
        db.session.commit()
        db.session.refresh(user_registration)
        db.session.refresh(event)
        db.session.refresh(hacker)
        return {
            "success": True,
            "event_id": event.id,
            "hacker_id": hacker.id,
            "hacker_name": hacker.name,
            "hacker_shirt_size": user_registration.shirt_size,
            "food_restrictions": user_registration.food_restrictions,
            "message": message,
        }

    @BaseService.needs_service(HackerService)
    def unparticipate_hacker(self, event_id: int, hacker_code: str, data: BaseToken):
        if not data.is_admin:
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(event_id)
        if event.archived:
            raise InvalidDataException(
                "Unable to operate with an archived event, unarchive it first"
            )
        hacker = self.hacker_service.get_by_code(hacker_code)
        if hacker not in event.participants:
            raise InvalidDataException("Hacker not participating")
        event.participants.remove(hacker)
        db.session.commit()
        db.session.refresh(event)
        db.session.refresh(hacker)
        return event

    @BaseClient.needs_client(MailClient)
    @BaseService.needs_service(HackerService)
    def accept_hacker(self, event_id: int, hacker_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(event_id)
        if event.archived:
            raise InvalidDataException(
                "Unable to operate with an archived event, unarchive it first"
            )
        hacker = self.hacker_service.get_by_id(hacker_id)
        if hacker not in event.registered_hackers:
            raise InvalidDataException("Hacker not registered")
        if hacker in event.accepted_hackers:
            raise InvalidDataException("Hacker already accepted")
        hacker_registration = (
            db.session.query(HackerRegistration)
            .filter(
                HackerRegistration.user_id == hacker.id,
                HackerRegistration.event_id == event.id,
            )
            .first()
        )
        if hacker_registration is None:
            raise InvalidDataException("Hacker not registered")
        token = AssistenceToken(hacker, event.id).to_token()
        hacker_registration.confirm_assistance_token = token
        event.accepted_hackers.append(hacker)

        mail = self.mail_client.create_mail(
            MailCreate(
                template_id=self.mail_client.get_internall_template_id(
                    InternalTemplate.EVENT_HACKER_ACCEPTED
                ),
                subject="You have been accepted",
                receiver_id=str(hacker.id),
                receiver_mail=str(hacker.email),
                fields=f"{hacker.name},{event.name},5,{token}",
            )
        )
        self.mail_client.send_mail_by_id(mail.id)
        db.session.commit()
        db.session.refresh(event)
        db.session.refresh(hacker)
        return event

    @BaseService.needs_service(HackerService)
    def unaccept_hacker(self, event_id: int, hacker_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(event_id)
        if event.archived:
            raise InvalidDataException(
                "Unable to operate with an archived event, unarchive it first"
            )
        hacker = self.hacker_service.get_by_id(hacker_id)
        if hacker not in event.accepted_hackers:
            raise InvalidDataException("Hacker not accepted")
        event.accepted_hackers.remove(hacker)
        db.session.commit()
        db.session.refresh(event)
        db.session.refresh(hacker)
        return event

    @BaseService.needs_service("HackerGroupService")
    def reject_group(self, event_id: int, group_id, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(event_id)
        if event.archived:
            raise InvalidDataException(
                "Unable to operate with an archived event, unarchive it first"
            )
        group = self.hackergroup_service.get_by_id(group_id)
        for hacker in group.members:
            if hacker not in event.accepted_hackers:
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
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(event_id)
        if event.archived:
            raise InvalidDataException(
                "Unable to operate with an archived event, unarchive it first"
            )
        hacker = self.hacker_service.get_by_id(hacker_id)
        if hacker not in event.registered_hackers:
            raise InvalidDataException("Hacker not registered")
        if hacker in event.accepted_hackers:
            raise InvalidDataException("Hacker already accepted")
        event.rejected_hackers.append(hacker)
        db.session.commit()
        db.session.refresh(event)
        db.session.refresh(hacker)
        return event

    @BaseService.needs_service("HackerGroupService")
    def accept_group(self, event_id: int, group_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(event_id)
        if event.archived:
            raise InvalidDataException(
                "Unable to operate with an archived event, unarchive it first"
            )
        group = self.hackergroup_service.get_by_id(group_id)
        for hacker in subtract_lists(group.members, event.accepted_hackers):
            if hacker not in event.registered_hackers:
                raise InvalidDataException("Hacker not registered")
            hacker_user = self.hacker_service.get_by_id(hacker.id)
            self.accept_hacker(event.id, hacker_user.id, data)

    @BaseService.needs_service(MailClient)
    def resend_mails(self, event_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(event_id)
        if event.archived:
            raise InvalidDataException(
                "Unable to operate with an archived event, unarchive it first"
            )
        for hacker in event.accepted_hackers:
            hacker_registration = (
                db.session.query(HackerRegistration)
                .filter(
                    HackerRegistration.user_id == hacker.id,
                    HackerRegistration.event_id == event.id,
                )
                .first()
            )
            token = AssistenceToken(hacker, event.id).to_token()
            hacker_registration.confirm_assistance_token = token

            self.mail_client.create_mail(
                MailCreate(
                    template_id=self.mail_client.get_internall_template_id(
                        InternalTemplate.EVENT_HACKER_ACCEPTED
                    ),
                    subject="You have been accepted",
                    receiver_id=str(hacker.id),
                    receiver_mail=str(hacker.email),
                    fields=f"{hacker.name},{event.name},5,{token}",
                )
            )

        db.session.commit()

    @BaseService.needs_service(MailClient)
    @BaseService.needs_service(HackerService)
    def resend_mail(self, event_id: int, hacker_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(event_id)
        if event.archived:
            raise InvalidDataException(
                "Unable to operate with an archived event, unarchive it first"
            )

        hacker = self.hacker_service.get_by_id(hacker_id)

        hacker_registration = (
            db.session.query(HackerRegistration)
            .filter(
                HackerRegistration.user_id == hacker.id,
                HackerRegistration.event_id == event.id,
            )
            .first()
        )
        token = AssistenceToken(hacker, event.id).to_token()
        hacker_registration.confirm_assistance_token = token

        self.mail_client.create_mail(
            MailCreate(
                template_id=self.mail_client.get_internall_template_id(
                    InternalTemplate.EVENT_HACKER_ACCEPTED
                ),
                subject="You have been accepted",
                receiver_id=str(hacker.id),
                receiver_mail=str(hacker.email),
                fields=f"{hacker.name},{event.name},5,{token}",
            )
        )

        db.session.commit()

    @BaseService.needs_service(MailClient)
    def send_slack_mail(self, event_id: int, slackUrl: str, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(event_id)
        if event.archived:
            raise InvalidDataException(
                "Unable to operate with an archived event, unarchive it first"
            )

        hackers = event.accepted_hackers

        for hacker in hackers:
            mail = self.mail_client.create_mail(
                MailCreate(
                    template_id=self.mail_client.get_internall_template_id(
                        InternalTemplate.EVENT_SLACK_INVITE
                    ),
                    subject="HackEPS2024 slack invitation",
                    receiver_id=str(hacker.id),
                    receiver_mail=str(hacker.email),
                    fields=slackUrl,
                )
            )
            # send the created mail
            self.mail_client.send_mail_by_id(mail.id)

        db.session.commit()

    @BaseService.needs_service(MailClient)
    def send_reminder_mails(
        self,
        event_id: int,
        data: BaseToken,
    ):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        event = self.get_by_id(event_id)
        if event.archived:
            raise InvalidDataException(
                "Unable to operate with an archived event, unarchive it first"
            )

        hackers = event.accepted_hackers

        for hacker in hackers:
            reg = (
                db.session.query(HackerRegistration)
                .filter(
                    HackerRegistration.user_id == hacker.id,
                    HackerRegistration.event_id == event.id,
                )
                .first()
            )
            # send reminder only if registration exists and assistance not confirmed
            if reg is None or reg.confirmed_assistance:
                continue

            # ensure there is a confirmation token for this registration
            if not reg.confirm_assistance_token:
                reg.confirm_assistance_token = AssistenceToken(hacker, event.id).to_token()

            # compute days left until event (rounded down)
            try:
                delta = event.start_date - datetime.now()
                days_left = max(0, int(delta.total_seconds() // 86400))
            except Exception:
                days_left = 0

            fields = f"{hacker.name},{event.name},{days_left},{reg.confirm_assistance_token}"

            mail = self.mail_client.create_mail(
                MailCreate(
                    template_id=self.mail_client.get_internall_template_id(
                        InternalTemplate.EVENT_HACKER_REMINDER
                    ),
                    subject=f"{event.name} - Recordatori de confirmació d'assistència",
                    receiver_id=str(hacker.id),
                    receiver_mail=str(hacker.email),
                    fields=fields,
                )
            )
            # send the created mail
            self.mail_client.send_mail_by_id(mail.id)
        db.session.commit()