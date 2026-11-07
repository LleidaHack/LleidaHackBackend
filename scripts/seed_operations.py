"""Create an isolated, repeatable local demonstration. Never targets production."""

import os
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

url = make_url(os.environ["DATABASE__URL"])
if url.host not in {"localhost", "127.0.0.1"} or url.database != "llh_operations_dev":
    raise SystemExit("Seed only supports the local llh_operations_dev database")
from src import imports  # noqa: F401
from src.impl.Event.model import Event, HackerRegistration
from src.impl.Hacker.model import Hacker
from src.impl.HackerGroup.model import HackerGroup
from src.impl.LleidaHacker.model import LleidaHacker
from src.impl.Meal.model import Meal
from src.impl.Operations.model import EventOperations, Presentation
from src.impl.Operations.schema import EventConfig
from src.impl.UserConfig.model import UserConfig
from src.impl.Voucher.model import Voucher
from src.utils.security import get_password_hash
from src.utils.Token import AccesToken, RefreshToken, ResetPassToken, VerificationToken

engine = create_engine(url)
with Session(engine) as session:
    if session.query(Event).filter_by(name="HackEPS Local Demo").first():
        print("Local demonstration already exists; data was preserved.")
        raise SystemExit(0)
    now = datetime.now(UTC)
    event = Event(
        name="HackEPS Local Demo",
        description="Local test data, not the real event",
        location="Demo campus",
        max_participants=100,
        max_group_size=4,
        max_sponsors=10,
        archived=False,
        is_open=True,
        price=0,
        start_date=now.replace(tzinfo=None),
        end_date=(now + timedelta(days=2)).replace(tzinfo=None),
    )
    session.add(event)
    session.flush()
    people = []
    for index in range(13):
        config = UserConfig(default_lang="ca")
        session.add(config)
        session.flush()
        values = {
            "name": "Local Organizer" if index == 0 else f"Participant {index:02d}",
            "nickname": f"demo-{index}",
            "email": "organizer@example.test"
            if index == 0
            else f"participant{index}@example.test",
            "telephone": f"600{index:06d}",
            "password": get_password_hash("LocalDemo2026!"),
            "birthdate": date(2000, 1, 1),
            "food_restrictions": "",
            "address": "",
            "shirt_size": "M",
            "code": f"DEMO{index:03d}",
            "config_id": config.id,
            "is_verified": True,
            "github": "",
            "linkedin": "",
        }
        if index == 0:
            user = LleidaHacker(
                **values,
                role="organizer",
                access_role="superadmin",
                nif="LOCAL-DEMO",
                active=True,
                accepted=True,
            )
        else:
            user = Hacker(**values)
        session.add(user)
        session.flush()
        user.token = AccesToken(user).to_token()
        user.refresh_token = RefreshToken(user).to_token()
        user.verification_token = VerificationToken(user).to_token()
        user.rest_password_token = ResetPassToken(user).to_token()
        if index:
            session.add(
                HackerRegistration(
                    user_id=user.id,
                    event_id=event.id,
                    shirt_size="M",
                    food_restrictions="",
                    confirmed_assistance=True,
                )
            )
            event.accepted_hackers.append(user)
            if index < 12:
                event.participants.append(user)
                session.add(
                    Voucher(
                        event_id=event.id,
                        code=f"VDEMO{index:04d}",
                        hacker_id=user.id,
                        assigned_at=datetime.now(UTC).replace(tzinfo=None),
                    )
                )
            people.append(user)
        else:
            event.organizers.append(user)
    session.add(
        Meal(event_id=event.id, name="Sopar de prova", description="Local demo dinner")
    )
    session.add(
        Meal(
            event_id=event.id,
            name="Esmorzar de prova",
            description="Local demo breakfast",
        )
    )
    for index in range(5):
        session.add(Voucher(event_id=event.id, code=f"VTESTABC{index + 2}"))
    config = EventConfig(
        title="HackEPS Local Demo",
        deadline=now + timedelta(hours=24),
        judging_start=now + timedelta(hours=25),
        judging_end=now + timedelta(hours=29),
        phase="hacking",
        map_url="http://localhost:3000/demo-map.svg",
        map_notes="Mapa de demostració sense escala. No representa el recinte real.",
        challenges=[
            {
                "id": f"challenge-{i}",
                "title": f"Repte {i} · Cultivem idees",
                "description": "Repte de demostració. Substitueix aquest text des del panel.",
                "published": True,
                "resources": [
                    {"title": "Documentació de prova", "url": "https://example.org"}
                ],
            }
            for i in range(1, 6)
        ],
        rooms=[
            {"id": f"challenge-{i}", "title": f"Sala {i} · Repte {i}"}
            for i in range(1, 6)
        ]
        + [{"id": "mlh", "title": "Sala 6 · MLH"}],
        activities=[
            {
                "id": "workshop",
                "title": "Taller de tractors creatius",
                "start": now - timedelta(minutes=10),
                "end": now + timedelta(minutes=50),
                "location": "Espai de tallers",
                "points": 10,
            },
            {
                "id": "dinner",
                "title": "Sopar",
                "start": now + timedelta(hours=1),
                "end": now + timedelta(hours=2),
                "location": "Menjador",
                "points": 0,
            },
        ],
        faqs=[
            {
                "question": "Com aconsegueixo LleidaCoins?",
                "answer": "Participa en activitats i mostra l’acreditació a organització.",
            },
            {
                "question": "Com veig quan em toca presentar?",
                "answer": "Els torns apareixeran quan organització activi les presentacions.",
            },
        ],
        prizes=[
            {"id": "mug", "title": "Tassa HackEPS", "cost": 20, "stock": 5},
            {"id": "sticker", "title": "Adhesiu del tractor", "cost": 5, "stock": 50},
        ],
    )
    session.add(
        EventOperations(
            event_id=event.id, config=config.model_dump(mode="json"), version=0
        )
    )
    for index, user in enumerate(people):
        group = HackerGroup(
            name=f"Tractor Team {index + 1:02d}",
            description="Local demonstration team",
            leader_id=user.id,
            event_id=event.id,
            code=f"TEAM{index + 1:03d}",
            members=[user],
        )
        session.add(group)
        session.flush()
        room = f"challenge-{index % 5 + 1}"
        session.add(
            Presentation(
                event_id=event.id,
                group_id=group.id,
                room=room,
                track=room,
                position=index,
            )
        )
        if index % 2 == 0:
            session.add(
                Presentation(
                    event_id=event.id,
                    group_id=group.id,
                    room="mlh",
                    track="mlh",
                    position=index,
                )
            )
    session.commit()
    print(f"Created local event {event.id}, organizer and 12 participants.")
    print("Local login: organizer@example.test / LocalDemo2026!")
    print("Participant login: participant1@example.test / LocalDemo2026!")
    print("Scan DEMO001; DEMO012 is accepted but has not checked in.")
