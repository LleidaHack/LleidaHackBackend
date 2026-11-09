# Company judging portal

Each company has one shared email/password identity, separate from participant and organizer accounts. Multiple devices can remain signed in for seven days. Each event grant restricts the company to presentation rooms; a project must have a turn in an assigned room to be visible or editable. Evaluations are private to the company, never added to public Live snapshots.

Management creates/reissues invitations and revokes event access at `/v1/company-portal/manage/{event_id}`. Invitation creation is idempotent by operation UUID and queues mail outside the HTTP request. Links expire after 48 hours, are single use and carry their secret in a URL fragment. A new invitation invalidates earlier unused account links. Completing password setup/reset revokes all existing company sessions; ordinary login does not. Logout affects only the current session.

Notes, optional integer scores (0–10) and favorites belong to an event/company/project. Clients send the version they edited; stale updates return 409 with the current note and never overwrite it implicitly. Winner proposals are also versioned and remain private. Changing assigned rooms clears the proposal but preserves historical notes. Revocation preserves notes and denies future event requests.

## Local verification

Start the isolated operations environment using `scripts/local-operations.sh`. Then:

```sh
uv run --env-file .env.operations.local alembic upgrade head
uv run --env-file .env.operations.local python scripts/seed_company_portal.py
```

The seed rejects every database except local `llh_operations_dev`. It adds `company@example.test` / `LocalDemo2026!` without sending mail or overwriting existing notes. Open `http://localhost:3000/companies`. Start presentation turns from local Management to exercise the official timer. Never use demo credentials in production.

## Coordinated release

This release requires migration `20261109_company_portal` plus the Management and Live PRs. The migration adds five private portal tables and three optional project columns; it does not modify participant, voucher or meal records. Existing project exports remain compatible. Description, repository and demo CSV columns are optional and preserved on reimport when omitted. URLs are validated but never fetched by the importer.

1. Verify a fresh off-host backup of the main database, mail database and Compose/environment configuration, with checksums and a restore rehearsal. Record the current image and Alembic revision.
2. Use a reviewed migration deployment window: stop application writers/workers, run `alembic upgrade head` using the new image against the intended main database, verify the revision, then start the new API. The app-only `production_deploy.py` intentionally rejects unapplied migrations; do not bypass this check.
3. In the mail service environment, validate and provision `deploy/templates/company_portal_invitation.html` using `deploy/ensure_company_portal_template.py`, its SHA256, `--front-url https://live.hackeps.dev`, and the **mail** `DATABASE__URL`. Run without `--apply` first, then with it. The script refuses to change an existing differing template and verifies other rows are unchanged. It sends no email.
4. Set `COMPANY_PORTAL_ORIGIN=https://live.hackeps.dev` in the API environment. Configure `backend-company-mail-worker-main` from `deploy/compose-workers.example.yml` with the same image/environment/networks as the API. Verify mail credentials and template before starting it.
5. Publish the paired frontend releases after the API is ready. Use an explicitly approved test recipient for the first real invitation. Verify delivery, setup, two concurrent logins, project access, note conflicts and revocation before inviting companies.

The worker stores a durable mail ID before sending. It never automatically retries ambiguous creation/send outcomes. `uncertain` needs operator review. A process crash can leave `creating` or `sending`; inspect mail service state before issuing a new invitation. Reissuing invalidates the old link, but cannot recall a previously delivered email. Completed/expired deliveries clear the queued URL; database and mail service access must remain restricted. No delivery tokens are returned by management endpoints or logged by the worker.

For rollback, stop the new mail worker and return to compatible application images while keeping the additive schema and all new company data. Do not downgrade/drop portal tables or restore a stale backup over writes made after release. Schema downgrade exists for isolated rehearsals only.
