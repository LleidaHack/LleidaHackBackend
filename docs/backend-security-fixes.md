# Backend security fixes

Branch: `refactor-backend`.

## Implemented changes

| Audit finding | Change | Regression coverage |
| --- | --- | --- |
| F1 | Require the correct token purpose and current account state | `test_authentication.py` |
| F2 | Enforce team ownership, membership and organizer permissions | `test_permissions.py` |
| F3 | Filter profile, verification and nested ORM responses | `test_privacy.py` |
| F4 | Require independent JWT and service secrets of at least 32 characters | `test_privacy.py` |
| F5 | Exclude organizer NIF from general and public nested responses | `test_privacy.py` |
| F6 | Restrict company account creation and affiliation changes | `test_permissions.py` |
| F7 | Check stored tokens, rotate refresh atomically and revoke sessions | `test_authentication.py`, `test_password_reset.py` |
| F8 | Query the registration model and preserve omitted update fields | `test_registration_preferences.py` |
| F9 | Resolve preferences by user ID for both reads and updates | `test_registration_preferences.py` |
| F10 | Accept reset credentials in JSON and share password validation | `test_password_reset.py`, frontend service tests |
| F11 | Disable debug responses and remove credentials from token errors | `test_privacy.py` |

Tests use the real HTTP routes and PostgreSQL schema created by Alembic. Mail is
mocked before application initialization. The test setup must only target a
throwaway database; see `tests/README.md`.

## Client changes

- `POST /v1/auth/confirm-reset-password` requires a JSON body containing `token`
  and `password`. The frontend change is committed separately on its
  `refactor-backend` branch. Query-string passwords are no longer accepted.
- `/v1/auth/me` returns a restricted profile. Verification returns only
  `{ "success": true }`. Credentials are only returned by explicit credential
  issuance flows.
- Company signup requires organizer authentication. Self-service profile edits
  reject `company_id` and `role`; the existing company membership endpoint is
  restricted to organizers and invalidates a transferred user's session.
- `GET` and `PUT /v1/userConfig/{userId}` both interpret the identifier as a user
  ID, regardless of the associated configuration ID.
- General organizer profiles no longer include NIF. Event group listings do not
  expose invitation codes. Administrative and public nested responses filter
  credentials too.
- An existing valid access token can read the safe pending-verification profile.
  Business operations and refresh require an available, verified account.
- Blocking, deactivating or changing a password revokes the stored access and
  refresh tokens. Re-enabling the account requires a new login. The existing
  single-session model is retained.

## Release procedure

1. Supply independent strong `SECURITY__SECRET_KEY` and `SECURITY__SERVICE_TOKEN`
   values in each environment. Blank or sample settings now fail startup. Do not
   print their values when checking configuration.
2. If weak/default credentials were used, rotate them and update service clients.
   Rotating the signing key invalidates existing sessions and email tokens;
   arrange reissuance of pending verification, recovery and assistance links.
3. Coordinate the frontend reset contract change with the backend release.
4. Run the regression suite, then verify signup/verification, login/refresh,
   password recovery, team operations, registration and preferences in integration.
5. Deploy the exact tested commit. The deployment workflow now depends on the
   reusable PostgreSQL test workflow, rejects tracked server modifications and
   checks the server checkout's SHA. Deployments to the same branch are serialized.
6. Verify HTTP health and expected user flows after restart. Check error rates
   without recording credentials. Do not roll back to insecure secrets or code.

No database migration is needed for these changes. No production configuration,
remote branch, email service or live database was modified while implementing them.
The CI workflow has been configured locally; a hosted CI run and an integration or
production deployment have not been performed.

## Separate follow-up work

Shared rate limiting is implemented; see `request-protection.md`.
A mail outbox/queue, pagination, dependency vulnerability
scanning and infrastructure review remain separate follow-up work from the audit.
Existing SQLAlchemy relationship and Pydantic deprecation warnings are not resolved
by this patch.
