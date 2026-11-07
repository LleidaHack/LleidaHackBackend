"""Promote the first trusted organizer to superadmin after the access-role migrations.

The access-role migration moves every existing organizer to ``admin`` and creates
no superadmin, so role assignment, challenge release and other critical actions
are unavailable until this runs once.

Usage (on the production host, after ``alembic upgrade head``):

    DATABASE__URL=postgresql://... uv run python scripts/bootstrap_superadmin.py \
        organizer@example.org --reason "Initial production superadmin"

Refuses to run when a superadmin already exists unless ``--additional`` is given;
afterwards, assign further roles from Gestió (Users > role) instead.
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from src import imports  # noqa: F401
from src.impl.Operations.model import AccessRoleAudit
from src.impl.User.model import User


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("email")
    parser.add_argument("--reason", required=True)
    parser.add_argument(
        "--additional",
        action="store_true",
        help="Allow promoting even if a superadmin already exists",
    )
    args = parser.parse_args()
    if len(args.reason.strip()) < 3:
        raise SystemExit("--reason must have at least 3 characters")

    with Session(create_engine(os.environ["DATABASE__URL"])) as session:
        session.execute(text("SELECT pg_advisory_xact_lock(71465031)"))
        existing = (
            session.query(User)
            .filter(User.access_role == "superadmin", User.is_deleted.is_(False))
            .count()
        )
        if existing and not args.additional:
            raise SystemExit(
                f"{existing} superadmin(s) already exist; use Gestió or --additional"
            )
        user = (
            session.query(User)
            .filter(User.email == args.email, User.is_deleted.is_(False))
            .one_or_none()
        )
        if not user:
            raise SystemExit(f"No active user with email {args.email}")
        if user.access_role == "superadmin":
            raise SystemExit(f"{args.email} is already superadmin")
        previous = user.access_role
        user.access_role = "superadmin"
        session.add(
            AccessRoleAudit(
                actor_id=None,
                user_id=user.id,
                previous_role=previous,
                new_role="superadmin",
                reason=f"bootstrap: {args.reason.strip()}",
            )
        )
        session.commit()
        print(f"User {user.id} ({args.email}): {previous} -> superadmin")


if __name__ == "__main__":
    main()
