"""Public registration and management of HackEPS raffles."""

from secrets import SystemRandom

from fastapi import APIRouter, Depends, HTTPException
from fastapi_sqlalchemy import db
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import text

from src.utils.access import require_management
from src.utils.JWTBearer import JWTBearer

router = APIRouter(prefix="/raffles", tags=["Raffles"])


class RaffleName(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(min_length=2, max_length=120)


class Entry(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(min_length=2, max_length=150)
    email: str = Field(max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    phone: str = Field(pattern=r"^\+?[0-9]{9,15}$")
    postal_code: str = Field(pattern=r"^[0-9]{5}$")
    city: str = Field(min_length=1, max_length=100)

    @field_validator("phone", mode="before")
    @classmethod
    def compact_phone(cls, value):
        return value.replace(" ", "") if isinstance(value, str) else value


class Draw(BaseModel):
    count: int = Field(gt=0, strict=True)


def manager(token=Depends(JWTBearer())):
    require_management(token)


def lock_open(raffle_id):
    row = db.session.execute(
        text("SELECT drawn_at FROM raffle WHERE id=:id FOR UPDATE"), {"id": raffle_id}
    ).first()
    if row is None:
        raise HTTPException(404, "Sorteig inexistent.")
    if row.drawn_at:
        raise HTTPException(409, "Aquest sorteig ja s’ha tancat.")


@router.get("")
def catalogue():
    rows = db.session.execute(
        text("SELECT id, name, theme, drawn_at FROM raffle ORDER BY id")
    )
    return [dict(row) for row in rows.mappings()]


@router.post("/{raffle_id}/entries", status_code=201)
def enter(raffle_id: int, entry: Entry):
    lock_open(raffle_id)
    # Identical replies also avoid disclosing whether an email has registered.
    db.session.execute(
        text("""
        INSERT INTO raffle_entry (raffle_id, name, email, phone, postal_code, city)
        VALUES (:id, :name, :email, :phone, :postal_code, :city)
        ON CONFLICT (raffle_id, email) DO NOTHING
    """),
        {**entry.model_dump(), "id": raffle_id, "email": entry.email.lower()},
    )
    db.session.commit()
    return {"registered": True}


@router.get("/manage", dependencies=[Depends(manager)])
def manage():
    rows = db.session.execute(
        text("""
        SELECT r.id, r.name, r.drawn_at, count(e.id) AS entries,
               coalesce(json_agg(json_build_object(
                   'name', e.name, 'email', e.email, 'phone', e.phone
               ) ORDER BY e.winner_position)
               FILTER (WHERE e.winner_position IS NOT NULL), '[]'::json) AS winners
        FROM raffle r LEFT JOIN raffle_entry e ON e.raffle_id=r.id
        GROUP BY r.id ORDER BY r.id DESC
    """)
    )
    return [dict(row) for row in rows.mappings()]


@router.post("", status_code=201, dependencies=[Depends(manager)])
def create(body: RaffleName):
    raffle_id = db.session.execute(
        text("INSERT INTO raffle (name) VALUES (:name) RETURNING id"), body.model_dump()
    ).scalar_one()
    db.session.commit()
    return {"id": raffle_id}


@router.post("/{raffle_id}/draw", dependencies=[Depends(manager)])
def draw(raffle_id: int, body: Draw):
    lock_open(raffle_id)
    entries = list(
        db.session.execute(
            text("SELECT id FROM raffle_entry WHERE raffle_id=:id"), {"id": raffle_id}
        ).scalars()
    )
    if body.count > len(entries):
        raise HTTPException(422, "Hi ha menys participants que guanyadors demanats.")
    selected = SystemRandom().sample(entries, body.count)
    db.session.execute(
        text("UPDATE raffle_entry SET winner_position=:position WHERE id=:id"),
        [{"id": entry, "position": pos} for pos, entry in enumerate(selected, 1)],
    )
    db.session.execute(
        text("UPDATE raffle SET drawn_at=now() WHERE id=:id"), {"id": raffle_id}
    )
    db.session.commit()
    return {"count": len(selected)}
