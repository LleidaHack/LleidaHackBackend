"""Insert only the missing internal ticket template; never modify existing rows.

Supply a reviewed HTML file and its SHA-256. Defaults to validation only.
DATABASE__URL must point to the mail database; rehearse on a restore first.
"""

import argparse
import hashlib
import os
from pathlib import Path
from string import Template
from urllib.parse import urlsplit

import psycopg2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html", type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--front-url", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    raw = args.html.read_bytes()
    if hashlib.sha256(raw).hexdigest() != args.sha256:
        raise SystemExit("Template checksum mismatch")
    front = urlsplit(args.front_url)
    if (
        front.scheme != "https"
        or not front.hostname
        or front.username
        or front.query
        or front.fragment
    ):
        raise SystemExit("An explicit production HTTPS frontend URL is required")
    # This new template must work even before the old mail process is restarted.
    html = raw.decode().replace("$_front_link", args.front_url.rstrip("/"))
    template = Template(html)
    fields = [name for name in template.get_identifiers() if not name.startswith("_")]
    if not template.is_valid() or fields != ["name", "event_name", "code", "qr_url"]:
        raise SystemExit("Template fields do not match the backend's ticket sender")
    with (
        psycopg2.connect(os.environ["DATABASE__URL"]) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute("LOCK TABLE template IN SHARE ROW EXCLUSIVE MODE")
        cursor.execute(
            "SELECT id, md5(row_to_json(t)::text) FROM template t ORDER BY id"
        )
        before = dict(cursor.fetchall())
        cursor.execute(
            "SELECT id, html, is_active FROM template WHERE name = %s",
            ("event_hacker_ticket",),
        )
        found = cursor.fetchall()
        if found:
            if len(found) != 1 or found[0][1] != html or not found[0][2]:
                raise SystemExit(
                    "An existing ticket template differs: refusing to overwrite it"
                )
            print("Matching active ticket template already exists; no write needed")
            return
        if not args.apply:
            print(
                "Validated: ticket template is absent and can be inserted without editing existing rows"
            )
            return
        cursor.execute(
            "INSERT INTO template (creator_id, name, description, html, created_date, is_active, internal) VALUES (0, %s, %s, %s, CURRENT_DATE, true, true) RETURNING id",
            ("event_hacker_ticket", "HackEPS check-in ticket", html),
        )
        new_id = cursor.fetchone()[0]
        cursor.execute(
            "SELECT id, md5(row_to_json(t)::text) FROM template t WHERE id <> %s ORDER BY id",
            (new_id,),
        )
        if dict(cursor.fetchall()) != before:
            raise RuntimeError(
                "Existing template data changed; transaction will be rolled back"
            )
        print(
            f"Inserted ticket template {new_id}; all {len(before)} existing templates are unchanged. No mail was sent."
        )


if __name__ == "__main__":
    main()
