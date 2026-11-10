"""Read-only replication inventory. Does not promote or change PostgreSQL settings."""

import json
import os

import psycopg2


def inspect_connection(connection):
    with connection.cursor() as cursor:
        cursor.execute("SET TRANSACTION READ ONLY")
        cursor.execute("SET LOCAL statement_timeout = '3000ms'")
        cursor.execute("SELECT pg_is_in_recovery()")
        standby = cursor.fetchone()[0]
        result = {"role": "standby" if standby else "primary"}
        if standby:
            cursor.execute(
                "SELECT pg_last_wal_receive_lsn()::text, pg_last_wal_replay_lsn()::text, pg_is_wal_replay_paused()"
            )
            receive, replay, paused = cursor.fetchone()
            result.update(receive_lsn=receive, replay_lsn=replay, replay_paused=paused)
            cursor.execute("SELECT status FROM pg_stat_wal_receiver")
            result["receiver_states"] = [row[0] for row in cursor.fetchall()]
        else:
            cursor.execute(
                "SELECT application_name, state, sync_state, pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn)::bigint FROM pg_stat_replication"
            )
            result["replicas"] = [
                {"name": n, "state": state, "sync_state": sync, "replay_lag_bytes": lag}
                for n, state, sync, lag in cursor.fetchall()
            ]
            cursor.execute("SHOW synchronous_standby_names")
            result["synchronous_standby_names"] = cursor.fetchone()[0]
            cursor.execute("SHOW synchronous_commit")
            result["session_synchronous_commit"] = cursor.fetchone()[0]
        return result


if __name__ == "__main__":
    with psycopg2.connect(os.environ["DATABASE__URL"], connect_timeout=5) as connection:
        print(json.dumps(inspect_connection(connection)))
