"""Pacing and cross-worker exclusion for bulk mail jobs.

The Mail Backend logs into Gmail SMTP once per mail and Gmail throttles after
roughly a hundred rapid logins, so bulk senders wait between mails. Running
jobs are also tracked in memory per gunicorn worker; a Postgres advisory lock
per (event, job type) keeps a second worker from running the same job.
"""

import logging
import time
from contextlib import contextmanager

from sqlalchemy import text

logger = logging.getLogger(__name__)

# Minimum seconds between two mails of a bulk job. Tests set it to 0.
BULK_MAIL_MIN_INTERVAL = 2.0

# First advisory-lock key per job type; the second key is the event id.
BULK_JOB_LOCK_KEYS = {
    "slack": 76501,
    "discord": 76502,
    "reminder": 76503,
    "ticket": 76504,
}


def pace_bulk_mail(delay: float | None = 0.0):
    """Wait between two bulk mails: the requested delay, never below the minimum."""
    wait = max(float(delay or 0), BULK_MAIL_MIN_INTERVAL)
    if wait > 0:
        time.sleep(wait)


@contextmanager
def bulk_job_lock(engine, event_id: int, job_type: str):
    """Hold a session-level advisory lock on a dedicated connection.

    Yields True when this process owns the job, False when another worker is
    already running it. The lock is released (or its connection discarded)
    when the block exits, so it never leaks into the connection pool.
    """
    key = BULK_JOB_LOCK_KEYS[job_type]
    connection = engine.connect()
    try:
        acquired = connection.execute(
            text("SELECT pg_try_advisory_lock(:key, :event)"),
            {"key": key, "event": event_id},
        ).scalar()
        connection.commit()
        if not acquired:
            yield False
            return
        try:
            yield True
        finally:
            try:
                connection.execute(
                    text("SELECT pg_advisory_unlock(:key, :event)"),
                    {"key": key, "event": event_id},
                )
                connection.commit()
            # Never hand a connection that may still hold the lock back to the pool.
            except Exception:  # noqa: BLE001
                logger.warning("Releasing the %s job lock failed", job_type)
                connection.invalidate()
    finally:
        connection.close()


def bulk_job_running(session, event_id: int, job_type: str) -> bool:
    """Whether any worker currently holds the (event, job type) lock."""
    return bool(
        session.execute(
            text(
                "SELECT EXISTS (SELECT 1 FROM pg_locks WHERE locktype = 'advisory' "
                "AND granted AND database = (SELECT oid FROM pg_database "
                "WHERE datname = current_database()) AND classid::bigint = :key "
                "AND objid::bigint = :event AND objsubid = 2)"
            ),
            {"key": BULK_JOB_LOCK_KEYS[job_type], "event": event_id},
        ).scalar()
    )
