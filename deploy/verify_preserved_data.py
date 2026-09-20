"""Fingerprint every existing column/row and sequence before/after a migration.

Read-only: never prints row contents. Run against the isolated restore first.
DATABASE__URL is required; output contains only schema names, counts and hashes.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path

import psycopg2
from psycopg2 import sql


def snapshot(connection, baseline=None):
    result = {"tables": {}, "sequences": {}}
    with connection.cursor() as cursor:
        cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
        cursor.execute("SET timezone = 'UTC'")
        if baseline is None:
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' AND table_name <> 'alembic_version' ORDER BY table_name")
            tables = [row[0] for row in cursor.fetchall()]
        else:
            tables = baseline["tables"]
        for table in tables:
            if baseline is None:
                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position", (table,))
                columns = [row[0] for row in cursor.fetchall()]
            else:
                columns = baseline["tables"][table]["columns"]
            query = sql.SQL("SELECT row_to_json(r)::text FROM (SELECT {} FROM public.{}) r ORDER BY row_to_json(r)::text COLLATE \"C\"").format(
                sql.SQL(",").join(map(sql.Identifier, columns)), sql.Identifier(table))
            digest = hashlib.sha256()
            count = 0
            with connection.cursor(name="rows") as rows:
                rows.execute(query)
                for (row,) in rows:
                    digest.update(row.encode("utf-8") + b"\n")
                    count += 1
            result["tables"][table] = {"columns": columns, "count": count, "sha256": digest.hexdigest()}
        cursor.execute("SELECT sequencename FROM pg_sequences WHERE schemaname='public' ORDER BY sequencename")
        names = [row[0] for row in cursor.fetchall()] if baseline is None else baseline["sequences"]
        for name in names:
            cursor.execute(sql.SQL("SELECT last_value, is_called FROM public.{}").format(sql.Identifier(name)))
            result["sequences"][name] = list(cursor.fetchone())
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["capture", "compare"])
    parser.add_argument("baseline", type=Path)
    args = parser.parse_args()
    baseline = json.loads(args.baseline.read_text()) if args.mode == "compare" else None
    with psycopg2.connect(os.environ["DATABASE__URL"]) as connection:
        result = snapshot(connection, baseline)
    if baseline is None:
        with args.baseline.open("x") as output:
            json.dump(result, output, indent=2)
    elif result != baseline:
        changes = [name for name in baseline["tables"] if result["tables"][name] != baseline["tables"][name]]
        raise SystemExit(f"Data preservation FAILED: changed tables={changes}; sequences_equal={result['sequences'] == baseline['sequences']}")
    print(f"{args.mode}: {len(result['tables'])} tables, {sum(t['count'] for t in result['tables'].values())} rows, {len(result['sequences'])} sequences verified")


if __name__ == "__main__":
    main()
