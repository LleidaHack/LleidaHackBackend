# Production release preparation — updated 2026-09-23

## Scope and evidence

This release promotes the application changes from `refactor-backend` at
`a3ec633e11ab935fac7f151ee21c1ee624c0fa5d`. Production has **not** been migrated.
The preparation branch also replaces the obsolete systemd deployment with an
explicit Docker image preparation workflow. A push to main validates code; it
no longer restarts production. The manual workflow builds a candidate only.

Verified on the actual host:

- Production backend commit: `7cc19b0114558d16ace691f097ca40cf43334294`.
- Testing commit: `d120f91f9464c9b0fcbde4b8e84807b777457f37`, with five edited
  tracked files and one added upload helper. All six files exactly match the
  release source by SHA-256; no missing manual application fixes were found.
- Production Alembic revision: `eb5796b93841`; candidate: `20260918_vouchers`.
- PostgreSQL 15 production contains 615 users, 3 events and 682 registrations.
- A fresh custom-format dump of both main databases, static assets, effective
  container metadata and host configuration is held in the private release
  backup on the VPS and copied off-host. Database/config checksums match.
- Both database dumps restored successfully to isolated PostgreSQL 15.
- The two migrations succeeded on the restored backend database. SHA-256
  fingerprints of every pre-existing column in all 28 application tables
  (5,349 rows) and all 10 sequences were identical before and after migration.
  Alembic's version table is intentionally excluded. New columns/tables are
  excluded from the preservation comparison, not from Alembic migration.
- Mail restore: 3,176 messages and 8 templates.
- Backend regression suite: 114 passed. HTTP smoke checks against restored data:
  OpenAPI and the 2024/2025 public event endpoints returned 200; unauthenticated
  profile returned 401. Mail was mocked, so these checks sent no emails.
- A non-root Docker candidate built and passed import validation on the VPS.
  The Dockerfile now makes application files readable even when the source
  checkout was created with a private umask.
- Hosted backend tests, security scanning and CodeQL passed on the earlier preparation
  PR. The inherited 1,215 Ruff findings were resolved on September 23; see the
  updated evidence below for final checks.
- Build cache cleanup recovered approximately 20 GB; host had 25 GB free after
  cleanup. Existing application containers and database volumes were retained.
- Current backend/mail images are additionally tagged
  `lleidahack/backend-rollback:20260920` and
  `lleidahack/mail-rollback:20260920`.

## September 23 validation and remaining cutover work

- Backend-only scope: the owner explicitly excluded frontend/Vercel work.
  Confirmed backend origins remain hackeps.dev, gestio.hackeps.dev and
  qr.hackeps.dev. DNS/frontend changes are outside this preparation.
- Fresh backend and mail dumps are held at `/root/backups/release-20260923/`
  and `/Users/bepeslabs/.codex/private/llh-release-20260923/release-20260923/`.
  Both off-host SHA-256 checks passed and both dumps restored to isolated PG15.
  The new backend restore migrated to `20260918_vouchers`; all 28 existing
  tables, 5,349 rows and 10 sequences match their pre-migration fingerprints.
- Ruff 0.16.8 is pinned. Maintained Python code passes lint and format checks;
  generated client code is excluded. Existing datetime and service-boundary
  behavior is retained explicitly. OpenAPI before and after the lint cleanup
  is byte-identical after JSON key sorting. Regression suite: **118 passed**.
- Four actual Uvicorn proxy-middleware tests verify trusted proxy extraction,
  forged X-Forwarded-For prefixes, untrusted peers and IPv6. NPM appends the
  client address; Uvicorn selects the rightmost untrusted address. Trust only
  NPM's current production-network IP, `172.18.0.7`, and revalidate after changes.
- `deploy/ensure_ticket_template.py` was rehearsed twice on restored mail data
  (insert, then no-op), then added ticket template 9 to the production mail DB.
  All eight existing templates remain byte-identical; no emails were sent.
  The insertion is transactional, checksum-gated and refuses conflicting rows.
- `deploy/prepare_mail_config.py` staged the current mail image by immutable ID,
  corrected FRONT_URL to https://hackeps.dev, and preserved effective SMTP/DB
  settings in private files at
  `/root/LleidaHackWeb/releases/mail/preparation-20260923/`.
  It does not restart mail or run migrations. Apply this configuration during
  the coordinated cutover; old mail processes still use the previous URL.
- JWT and service keys exposed in old tracked history must rotate at cutover.
  Independent replacements are staged privately; existing sessions and signed
  email links will need reissuance. Update dependent service clients then.
- Final hosted CI must pass. GitHub deployment SSH secrets have not been
  exercised; preparation used a separate authenticated SSH session.
- Production backend is still the original image and schema. There has been no
  merge, backend restart or production schema migration. Deprecation warnings
  remain; no production SMTP-delivery test is claimed.

## Prepare an immutable Docker candidate

Run from a clean checkout on the VPS with the full reviewed commit, never a
moving branch. This builds an image but does not contact the production database:

```sh
bash deploy/prepare-docker-release.sh "$SHA" "$RELEASE"
python3 deploy/prepare_production_config.py "$SHA" "$RELEASE" \
  --rotate-secrets --front-url https://hackeps.dev \
  --origins '["https://hackeps.dev","https://gestio.hackeps.dev","https://qr.hackeps.dev"]'
```

The second command writes mode-600 `runtime.env` and `compose.json`, preserves
static files, pins the available Redis image by digest and uses the existing
external production network. It refuses to overwrite an existing preparation.
Treat the whole release directory as private. Never commit/upload its runtime
files to GitHub. Compose >=2.30 is required for `env_file.format: raw` (host 2.37.3).
The prepared Compose configuration contains no database service or data volume:
there is nothing in it that can replace the production database volume.
It preserves the existing database URL and database credentials; application
JWT and service keys are staged separately for coordinated rotation. Frontend URLs/origins
must be reviewed before it is used. Database migration is deliberately absent
from the replacement backend's startup command.

## Final cutover, only after the gates pass

1. Record the final source SHA and built image ID; preserve the running image,
   original Compose/configuration, database volumes and static files. Check
   `docker compose -f "$RELEASE/compose.json" config --quiet` (do not print config).
2. Put the backend behind maintenance and stop all application writers to main.
   Drain in-flight requests/jobs. Keep PostgreSQL running. Refresh static copies
   if they changed. Do not copy testing databases into production.
3. Make new backend and mail database backups during the write freeze, checksum
   them and copy them off-host. The earlier rehearsal backup is not the final
   cutover backup. Record a fresh preservation baseline before migration with
   `deploy/verify_preserved_data.py capture`, using the main database URL via
   private environment and an output file outside the repository.
4. Redis-main was provisioned on the private production network during preparation.
   Start only Redis with the prepared Compose file if it is not already running. Verify health, private
   network exposure, `maxmemory 64mb` and `maxmemory-policy noeviction`.
5. Run `alembic upgrade head` explicitly using the candidate image and private
   runtime environment on the production network. Stop on any error. Compare
   the fresh baseline with `verify_preserved_data.py compare` before reopening
   writes. Confirm revision `20260918_vouchers` and new schema objects.
6. Start **only** the replacement backend-main service using the prepared Compose
   file, with `--no-deps`. Never use `down -v`, `--remove-orphans`, schema reset,
   `pg_restore --clean`, or a testing database URL. Other services stay in place.
7. Start only mail-backend-main with its prepared Compose file and `--no-deps`
   to activate corrected email links, without running mail migrations. Preserve
   the mail database and SMTP configuration. Verify template reads without
   sending mail.
8. Update the authoritative host deployment configuration to use the prepared
   image/configuration, so a later invocation of the old Compose build cannot
   revert the release. Keep its database services/volumes unchanged.
   Verify internal and public HTTP health, CORS, mail template availability,
   login/refresh, recovery, edition data and organizer/check-in flows. Reopen
   writes only when checks pass; observe errors and Redis 429/503 rates.

## Recovery without discarding new writes

Before reopening writes, a failed migration/validation keeps the system under
maintenance; investigate against the preserved backup and schema state.
The migrations are additive, so prefer returning to the previous application
image while keeping the upgraded database, after verifying compatibility in
rehearsal. Do not automatically downgrade migrations: downgrade deletes new
columns and voucher data.

After writes resume, **never restore an earlier full database dump over main**
as a routine rollback. That would discard new registrations and edits. Preserve
current data, roll back application code where compatible, and forward-fix or
perform an explicitly reviewed data reconciliation if schema repair is needed.

## Private artifacts

VPS backup: `/root/backups/release-20260920/`.
Off-host backup: `/Users/bepeslabs/.codex/private/llh-release-20260920/`.
The temporary local restored database is bound to loopback only; it is not a
public staging environment and must never run the destructive pytest fixtures.
Remove the temporary restore once final validation is complete; retain backups
according to the release retention policy.
