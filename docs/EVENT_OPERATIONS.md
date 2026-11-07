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
