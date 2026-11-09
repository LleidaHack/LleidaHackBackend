# Event operations and local integration

The backend owns access roles, event configuration, meal rounds, attendance, the coin ledger, presentation queues, alert delivery and audit records. `llh-admin` manages these records; HackEPS provides the staff scanner and participant wallet; `life-page` renders public event data. Deploy the coordinated branches together after review. No production migration or deployment is part of this change.

## Local setup

Requires Docker and uv. Run `bash scripts/local-operations.sh` in this repository. This creates isolated Postgres (55439), Redis (56379), ignored local credentials, migrates `llh_operations_dev`, seeds the demo, and serves the API on port 8000. Tests use a separate disposable database named `lleidahack_test`; never point test configuration at real data.

Demo passwords are `LocalDemo2026!`: `organizer@example.test` (superadmin), `admin@example.test`, `lleidahacker@example.test`, and `participant1@example.test` through `participant12@example.test`. Participant code `DEMO001` and badge `VDEMO0001` are sample data only. The seed commands deliberately work only against the named local database. Re-running the role seed restores staff demo roles.

Start the sibling applications in separate terminals:

```sh
# llh-admin
API_TARGET=http://127.0.0.1:8000 NEXT_PUBLIC_API_ORIGIN=http://localhost:8000 NEXT_PUBLIC_ENVIRONMENT_LABEL='Local demo' npm run dev -- --port 5175
# hackeps/hackeps
BROWSER=none HOST=127.0.0.1 PORT=3001 REACT_APP_DOMAIN=http://localhost:8000 REACT_APP_ADMIN_URL=http://localhost:5175 pnpm start
# life-page/frontend/live-page
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 NEXT_PUBLIC_EVENT_ID=1 NEXT_PUBLIC_ADMIN_URL=http://localhost:5175 npm run dev -- --port 3000
```

## Roles

| Role | Access |
| --- | --- |
| superadmin | Management, role assignment, manual coin awards, corrections, reward rules, deadlines and destructive actions |
| admin | Operational management, content, queues, meal rounds and alerts; no role assignment, manual coin adjustment or critical settings |
| lleidahacker | HackEPS scanner: check-in, badge assignment, meals, activities and prize redemption; no management access |
| hacker | Own participant profile, wallet, team selection and presentation schedule |

Access roles live on the base user and do not change the legacy polymorphic account type, job title, team or registration. Every authenticated request resolves roles from the database so revocations affect existing tokens. Only superadmins can PATCH `/v1/access/users/{id}/role`, with a reason. Changes are recorded in `access_role_audit`. Self-demotion and removal of the last available superadmin are rejected. The first production superadmin must be explicitly provisioned through a controlled operator action; migrations preserve existing organizers as admins, never silently promote them to superadmin. Local seed scripts must never be used in production.

## Event rules

Configure Live content, Slack, the actual venue map, FAQs, activities, rewards, rooms and judging dates in the event's operations tab. The demo map is explicitly unscaled sample artwork. Five challenge rooms and optional MLH are supported. Each team chooses one challenge plus optional MLH; generated schedules avoid room/team conflicts and preserve fixed turns. Superadmins can override conflicts with a recorded reason. Public judging details appear only during the judging phase.

Meals allow one collection per participant per round. Opening another round allows one additional collection. Old scans stay in the audit trail. Corrections void scans or create opposite ledger entries, rather than deleting evidence. Activity rewards come from server configuration. Scans use operation UUIDs; identical retries return the original result, while changed payloads with the same UUID are denied. The event row lock serializes rewards/redemptions and prevents concurrent double-spends. Client-supplied coin values cannot set activity rewards. Tampering gets a tractor-themed rejection and no reward.

## Alert channels

Gestió supports general, activity and meal announcements, an expiry duration and independent destinations: Live/screens, Web Push and the official Discord bot.

- Live alerts travel over `/v1/operations/{event_id}/ws` using Redis pub/sub across API workers. Clients reconnect and retain a 3-second HTTP snapshot fallback. WebSocket messages contain only public alerts; they cannot change state. Configure reverse proxies for WebSocket upgrades and HTTPS/WSS. Redis uses the configured rate-limit Redis URL and prefix.
- Push delivery uses a durable outbox. Configure `VAPID_PRIVATE_KEY`, `VAPID_PUBLIC_KEY`, `VAPID_SUBJECT`, then run `uv run python -m src.impl.Operations.push_worker`. For local development only, `uv run --env-file .env.operations.local python scripts/configure_local_push.py` generates the ignored VAPID credentials. Restart the API afterward and start the worker with the local env file. Browser permission and a supported secure context are required. Actual mobile delivery still needs a device test.
- Discord alerts are queued immediately, even before the future bot is connected. Gestió shows queued, leased, sent, failed, expired and cancelled states. A queued alert is not a delivered Discord message. See [Discord bot integration](DISCORD_BOT_INTEGRATION.md). No Discord credentials or real channel messages are included in the local demo.

Withdrawing an alert removes it from Live and cancels pending deliveries. It cannot retract a push already shown or a message already sent to Discord; a bot that has already claimed work may race cancellation. Announcements should be corrected explicitly when already delivered.

## Validation and rollout limits

Backend regression coverage includes role changes/revocation, authorization, forged awards, concurrent scans/redemptions, meal rounds/corrections, scheduling, WebSocket alerts and Discord delivery leases/acknowledgements. Run `uv run pytest -q` with isolated Postgres and Redis available. Existing SQLAlchemy relationship and Pydantic deprecation warnings remain.

Before an authorized production rollout: back up and rehearse the Alembic migration chain; explicitly bootstrap a trusted superadmin; configure real event content and origins; enable WebSocket proxying; run the push worker; connect the separately implemented Discord bot. Verify phone camera scanning, installed-PWA notifications and Raspberry Pi display/fullscreen behavior on actual hardware. These physical checks are not replaced by browser/API tests.

### Production rollout checklist

`deploy/production_deploy.py` refuses releases that touch `alembic/`, so this release follows the manual migration runbook:

1. Back up the database. Check `SELECT to_regclass('public.mentor'), to_regclass('public.mentor_event_participation');` returns NULLs (migration `20261106_event_mentors` creates them).
2. Run `alembic upgrade head` **before** starting the new image. New code on the old schema fails every authenticated request (`my_user.access_role` is missing). The previous image keeps working on the new schema, so rolling the image back does not require a downgrade; downgrades drop audit, ledger and revocation data — restore the backup instead.
3. Bootstrap the first superadmin immediately (every existing organizer becomes `admin`, which cannot assign roles, release challenges, ban users or delete records):
   `uv run python scripts/bootstrap_superadmin.py organizer@example.org --reason "Initial production superadmin"`
   Then assign further roles from Gestió.
4. Configure optional integrations: `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT` (push), `DISCORD_WEBHOOK_URL`, `DISCORD_WEBHOOK_EVENT_ID` (webhook announcements).
5. Run the workers as separate long-lived services from the same image: copy `deploy/compose-workers.example.yml` into the production Compose file (`backend-push-worker-main`, `backend-discord-worker-main`). `deploy/production_deploy.py` then updates and rolls them back together with `backend-main`. Without them alerts are queued but never delivered.
6. Proxy WebSocket upgrades for `/v1/operations/{event_id}/ws` (`proxy_http_version 1.1`, `Upgrade`/`Connection` headers).
7. Deploy the clients afterwards: Gestió (llh-admin), HackEPS and Live.

## Printed accreditations (vouchers)

Each printed badge carries a voucher QR. Hackers' badges are bound when their ticket is scanned at check-in; mentors' badges are bound from the mentor roster. In Gestió → Check-in, generate all the vouchers at once and export the CSV (ordered by creation). Then merge the artwork with one unique QR per badge. Consecutive slices of the same CSV feed the differently coloured badges, so no code is printed twice:

```sh
# 2026 artwork (social-final): the QR fills the rounded white square, no code text
Q=(--width-mm 90 --x 119.5 --y 944 --size 282 --no-code --quiet-zone 1 --no-fill)
# Proof: one page, the QR square outlined in red
uv run python scripts/badge_print.py hackers-green/front.png vouchers.csv $Q --limit 1 --outline -o proof.pdf
# Print files: front + back per voucher
uv run python scripts/badge_print.py hackers-green/front.png vouchers.csv --back hackers-green/back.png $Q --limit 260 -o hackers.pdf
uv run python scripts/badge_print.py mentors-companies-red/front.png vouchers.csv --back mentors-companies-red/back.png $Q --skip 260 --limit 40 -o staff.pdf
uv run python scripts/badge_print.py staff-yellow/front.png vouchers.csv --back staff-yellow/back.png $Q --skip 300 --limit 40 -o mentors-companies.pdf
```

PNG/JPEG artwork takes positions in image pixels; `--width-mm` sets the printed (trim) width and `--bleed-mm` (default 3) extends the edge pixels outwards for the cut. PDF designs take positions in millimetres from the top-left of the trim box. The QR must print at least 20 mm wide. It is vector, uses error correction level H and encodes exactly the voucher code; the code is printed under it for manual entry (`--no-code` omits it). `--quiet-zone` sets the white margin in modules (default 2) and `--no-fill` keeps artwork with rounded corners intact instead of painting the square white. `--only-unassigned` reprints spares without already bound vouchers.

## Public LleidaCoins leaderboard

The public event snapshot includes `leaderboard`, the top 50 participants with ledger activity ordered by current event balance. Redemptions reduce that balance and reversals restore it. Ties share competition ranks (1, 1, 3), with a stable alias/ID ordering. Only rank, public nickname and balance are exposed; deleted or banned participants are omitted. Events are isolated. Live shows the top 10 on its home page and the top 50 at `/leaderboard`, refreshing every three seconds.

Live home-page metadata includes `stream_url`, `wifi_name`, `wifi_instructions` and `wifi_guide_url` in event configuration/public snapshots. These fields are public and must not contain organizer-only credentials. Alerts carry their `event_id` so the service worker can forward foreground pushes to the matching Live page and deduplicate them with WebSocket messages.


## Preliminary team challenge choices

Migration `20261106_challenge_votes` adds a single choice per event/team, independent from Devpost projects and presentation enrollment. New event configurations start with challenges hidden and choices closed. Existing configurations without the new publication field preserve their previous per-challenge visibility; voting always starts closed.

Management uses `PUT /v1/operations/{event_id}/challenge-controls` with the event configuration version, `challenges_released`, `challenge_votes_open`, and a reason. Opening requires at least one published non-MLH challenge. The public operations snapshot and participant choice list omit unreleased challenges. The normal config update applies the same open/publication invariant.

Current group members use GET/PUT `/v1/operations/{event_id}/teams/{group_id}/challenge-vote`. PUT carries a challenge ID and the current team choice version (0 initially). The event lock serializes votes and management changes; the group relation is checked server-side. Outsiders, former members, hidden challenges, closed votes and stale versions are rejected. A database constraint allows one row per team. Changes increment the vote version and create a `challenge.vote` audit with actor and previous/new challenge. No points, submissions or judging turns are created.

GET `/v1/operations/{event_id}/challenge-votes` is restricted to management and returns per-challenge counts and per-team choices. Publication controls create `challenge.controls` audit entries. Hiding or closing retains existing choices. An imported Devpost submission does not silently replace the team's preliminary choice.

## Manual YouTube broadcast

Comunicació → Live accepts a YouTube video URL and a **Mostrar retransmissió** switch. Save to publish or hide the embedded player. The switch defaults to false and requires a valid YouTube video link when enabled. Organizers must disable it after the stream ends; no automatic live-status detection or Google API key is involved. Live starts playback muted, subject to browser policy. Deploy the backend configuration update before the clients; the JSON configuration requires no database migration.
