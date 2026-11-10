"""Seed an isolated event rehearsal using voucher codes, never production people."""

import argparse
import base64
import csv
import html
import io
import json
import os
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import segno
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from src import imports  # noqa: F401
from src.impl.Company.model import Company
from src.impl.CompanyPortal.model import PortalAccount, PortalGrant
from src.impl.Event.model import Event, HackerRegistration
from src.impl.Hacker.model import Hacker
from src.impl.HackerGroup.model import HackerGroup
from src.impl.LleidaHacker.model import LleidaHacker
from src.impl.Meal.model import Meal
from src.impl.Operations.model import (
    DevpostProject,
    EventMentor,
    EventOperations,
    Presentation,
)
from src.impl.Operations.schema import EventConfig
from src.impl.UserConfig.model import UserConfig
from src.impl.Voucher.model import Voucher
from src.utils.security import get_password_hash
from src.utils.Token import AccesToken, RefreshToken, ResetPassToken, VerificationToken

PASSWORD = "LocalDemo2026!"
COMPANIES = [
    (
        "rodi",
        "Rodi",
        "Mobilitat sense sorpreses",
        "Ajuda a anticipar el manteniment d’un vehicle amb dades simulades i recomanacions entenedores.",
    ),
    (
        "vallcompanys",
        "Vall Companys",
        "Menys malbaratament alimentari",
        "Proposa una eina per planificar producció i reduir excedents utilitzant dades fictícies.",
    ),
    (
        "openfort",
        "Openfort",
        "Recompenses sense complicacions",
        "Crea una experiència de recompenses digitals fàcil d’utilitzar per a persones sense coneixements tècnics.",
    ),
    (
        "jetbrains",
        "JetBrains",
        "El company de desenvolupament",
        "Dissenya una eina que ajudi un equip a entendre errors i millorar el seu flux de desenvolupament.",
    ),
    (
        "paeria",
        "La Paeria",
        "Una Lleida més accessible",
        "Facilita que la ciutadania trobi serveis i comuniqui barreres d’accessibilitat amb dades de prova.",
    ),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vouchers", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    url = make_url(os.environ["DATABASE__URL"])
    if (
        url.host not in {"localhost", "127.0.0.1"}
        or url.database != "llh_operations_dev"
    ):
        raise SystemExit("Rehearsal only supports local llh_operations_dev")
    with args.vouchers.open(newline="") as source:
        codes = [r["code"].strip() for r in csv.DictReader(source)]
    if (
        not codes
        or len(codes) != len(set(codes))
        or any(not c or len(c) > 100 for c in codes)
    ):
        raise SystemExit("Voucher CSV must contain unique nonempty codes")
    args.output.mkdir(parents=True, exist_ok=True, mode=0o700)
    now = datetime.now(UTC)
    title = "HackEPS Assaig Local"
    with Session(create_engine(url)) as session:
        existing = session.query(Event).filter_by(name=title).first()
        if existing:
            print(
                f"Rehearsal event {existing.id} already exists; all test activity preserved."
            )
            return
        collision = session.query(Voucher).filter(Voucher.code.in_(codes)).first()
        if collision:
            raise SystemExit(
                "Voucher codes already exist locally; no assignments were changed"
            )
        event = Event(
            name=title,
            description="Esdeveniment fictici per provar tota la jornada. No és producció.",
            location="Campus de prova",
            max_participants=100,
            max_group_size=4,
            max_sponsors=10,
            archived=False,
            is_open=True,
            price=0,
            start_date=now.replace(tzinfo=None),
            end_date=(now + timedelta(days=3)).replace(tzinfo=None),
        )
        session.add(event)
        session.flush()
        event.organizers.extend(
            session.query(LleidaHacker)
            .filter(
                LleidaHacker.access_role.in_(["superadmin", "admin", "lleidahacker"])
            )
            .all()
        )
        people = []
        records = []
        for i in range(1, 43):
            config = UserConfig(default_lang="ca")
            session.add(config)
            session.flush()
            mentor = i > 40
            dietary = {
                1: "Gluten",
                2: "Lactosa",
                3: "Fruits secs",
                4: "Vegetarià",
                5: "Vegà",
                6: "Sense porc",
            }.get(i, "")
            user = Hacker(
                name=f"{'Mentor' if mentor else 'Participant'} de prova {i:02d}",
                nickname=f"assaig-{i:02d}",
                email=f"{'mentor' if mentor else 'participant'}{i if not mentor else i - 40:02d}@hackeps.test",
                telephone=f"699{i:06d}",
                password=get_password_hash(PASSWORD),
                birthdate=date(2000, 1, 1),
                food_restrictions=dietary,
                address="Local demo",
                shirt_size=["S", "M", "L", "XL"][i % 4],
                code=f"LOCALHACK{i:04d}",
                config_id=config.id,
                is_verified=True,
                github="",
                linkedin="",
                access_role="mentor" if mentor else "hacker",
            )
            session.add(user)
            session.flush()
            user.token = AccesToken(user).to_token()
            user.refresh_token = RefreshToken(user).to_token()
            user.verification_token = VerificationToken(user).to_token()
            user.rest_password_token = ResetPassToken(user).to_token()
            if mentor:
                session.add(
                    EventMentor(event_id=event.id, user_id=user.id, active=True)
                )
                state = "Mentor"
            else:
                session.add(
                    HackerRegistration(
                        user_id=user.id,
                        event_id=event.id,
                        shirt_size=user.shirt_size,
                        food_restrictions=dietary,
                        confirmed_assistance=i <= 36,
                        studies="Informàtica",
                        study_center="Universitat de prova",
                        location="Lleida",
                        description="Inscripció fictícia d’assaig",
                    )
                )
                if i <= 38:
                    event.accepted_hackers.append(user)
                state = (
                    "Acceptat i confirmat"
                    if i <= 36
                    else "Acceptat sense confirmar"
                    if i <= 38
                    else "Pendent d’acceptació"
                )
                people.append(user)
            records.append(
                {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "code": user.code,
                    "status": state,
                    "dietary": dietary,
                }
            )
        for name in ["Dinar", "Sopar", "Esmorzar"]:
            session.add(
                Meal(
                    event_id=event.id,
                    name=name + " d’assaig",
                    description="Àpat de prova local",
                )
            )
        for code in codes:
            session.add(Voucher(event_id=event.id, code=code, revoked=False))
        challenges = []
        rooms = []
        company_logins = []
        for order, (slug, name, challenge, description) in enumerate(COMPANIES):
            company = Company(
                name=name,
                description="Patrocinador de mostra per a l’assaig local",
                address="Local demo",
                telephone="",
                website="https://example.test",
                image="",
                linkdin="",
                tier=1,
            )
            session.add(company)
            session.flush()
            event.sponsors.append(company)
            account = PortalAccount(
                company_id=company.id,
                email=slug + "@hackeps.test",
                password_hash=get_password_hash(PASSWORD),
                active=True,
            )
            session.add(account)
            session.flush()
            session.add(
                PortalGrant(
                    account_id=account.id, event_id=event.id, rooms=[slug], active=True
                )
            )
            company_logins.append(
                {"company": name, "email": account.email, "room": slug}
            )
            rooms.append({"id": slug, "title": "Sala " + name, "paused": False})
            challenges.append(
                {
                    "id": slug,
                    "company": name,
                    "title": challenge,
                    "description": description + " Repte fictici d’assaig, no oficial.",
                    "published": True,
                }
            )
        rooms.append({"id": "mlh", "title": "Sala MLH", "paused": False})
        for i in range(10):
            members = people[i * 4 : (i + 1) * 4]
            slug, name, challenge, _ = COMPANIES[i % 5]
            group = HackerGroup(
                name=f"Equip Assaig {i + 1:02d}",
                description="Projecte fictici de prova",
                leader_id=members[0].id,
                event_id=event.id,
                code=f"LOCALTEAM{i + 1:03d}",
                members=members,
            )
            session.add(group)
            session.flush()
            session.add(
                Presentation(
                    event_id=event.id,
                    group_id=group.id,
                    room=slug,
                    track=slug,
                    position=i // 5,
                    state="waiting",
                )
            )
            session.add(
                DevpostProject(
                    event_id=event.id,
                    group_id=group.id,
                    url=f"https://example.test/projecte-{i + 1}",
                    title=f"Prototip {i + 1:02d} · {challenge}",
                    challenge=slug,
                    description="Projecte de demostració: consulta’n els membres, afegeix notes i compara’l amb els altres equips.",
                    repository_url="https://example.test/repository",
                    demo_url="https://example.test/demo",
                    mlh=i < 3,
                )
            )
            if i < 3:
                session.add(
                    Presentation(
                        event_id=event.id,
                        group_id=group.id,
                        room="mlh",
                        track="mlh",
                        position=i,
                        state="waiting",
                    )
                )
        config = EventConfig(
            title=title,
            phase="hacking",
            deadline=now + timedelta(hours=24),
            judging_start=now,
            judging_end=now + timedelta(days=3),
            challenges_released=True,
            challenge_votes_open=True,
            challenges=challenges,
            rooms=rooms,
            wifi_name="ASSAIG-LOCAL",
            wifi_instructions="Entorn de proves al teu ordinador",
            activities=[
                {
                    "id": "taller",
                    "title": "Taller de prova",
                    "start": now - timedelta(minutes=10),
                    "end": now + timedelta(days=3),
                    "location": "Sala d’activitats",
                    "points": 10,
                }
            ],
            prizes=[
                {"id": "tassa", "title": "Tassa de prova", "cost": 20, "stock": 30},
                {"id": "adhesiu", "title": "Adhesiu de prova", "cost": 5, "stock": 100},
            ],
            faqs=[
                {
                    "question": "És l’esdeveniment real?",
                    "answer": "No. Aquest és un assaig local amb usuaris ficticis.",
                }
            ],
        )
        session.add(
            EventOperations(
                event_id=event.id, config=config.model_dump(mode="json"), version=0
            )
        )
        session.commit()
        event_id = event.id
    with (args.output / "participants.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    report = {
        "event_id": event_id,
        "vouchers": len(codes),
        "participants": 40,
        "mentors": 2,
        "teams": 10,
        "companies": company_logins,
        "password": PASSWORD,
    }
    (args.output / "rehearsal.json").write_text(json.dumps(report, indent=2))
    cards = []
    for person in records:
        if person["status"] == "Mentor":
            continue
        image = segno.make(person["code"], error="h")
        buffer = io.BytesIO()
        image.save(buffer, kind="png", scale=8, border=4)
        data = base64.b64encode(buffer.getvalue()).decode()
        cards.append(
            f"<article><h2>{html.escape(person['name'])}</h2><p>{html.escape(person['email'])}</p><img width='190' height='190' src='data:image/png;base64,{data}'><p>{person['code']}</p><p>{html.escape(person['status'])}</p><p>{html.escape(person['dietary'])}</p></article>"
        )
    (args.output / "tickets.html").write_text(
        "<!doctype html><html lang='ca'><meta charset='utf-8'><title>Entrades d’assaig local</title><style>body{font-family:system-ui;margin:24px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}article{border:1px solid #bbb;padding:16px;break-inside:avoid;text-align:center}h2{font-size:18px}p{overflow-wrap:anywhere}</style><h1>Entrades d’assaig local</h1><p>Escaneja primer aquesta entrada i després l’acreditació física. Contrasenya de totes les comptes de prova: LocalDemo2026!</p><main>"
        + "".join(cards)
        + "</main></html>"
    )
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
