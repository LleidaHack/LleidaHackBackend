# Public repository security review — 2026-09-16

Scope: tracked backend source, all locally available Git refs/history, Dockerfile,
GitHub workflows, locked Python dependencies and application regression tests.
Changes are on `refactor-backend`; they must be merged before they protect the
public default branch or a deployment. This is not a production penetration test.

## Findings and changes

- `.env` was tracked. Its current contents used environment substitutions, not
  confirmed live credentials, but tracking it risks future disclosure. Removed it
  from Git while preserving the local file; runtime env files, private keys and
  local generated credentials are ignored and excluded from Docker.
- Integration accepted a fixed fallback PostgreSQL password. It now requires an
  explicit database URL. JWT/service secrets reject placeholders and must differ.
- Docker cloned a branch during build, included its Git directory and ran as root.
  It now copies only runtime files from the reviewed checkout, uses the frozen
  production dependency lock, pins its base image by digest and runs as UID 10001.
  Development verification routes and mail capture tooling are absent from it.
- The container smoke check exposed an ORM import-order error hidden by the test
  setup. The production entry point now registers models before loading routers.
- CORS previously allowed all origins with credentials. It now uses an explicit
  `CORS_ORIGINS` JSON list (empty by default), explicit headers/methods and no cookie
  credentials. The isolated local launcher supplies localhost frontend origins.
- Debug logging was enabled. Application/Gunicorn logging now uses INFO and
  Gunicorn access logs are disabled because verification URLs contain tokens.
  Configure reverse-proxy logs to omit query strings too; do not log request bodies
  or Authorization headers. Existing application mail logs can still contain
  recipient addresses, so restrict log access/retention.
- Legacy manual installation/reset workflows used mutable actions, password SSH
  and incomplete/destructive scripts. They are disabled pending a reviewed
  replacement. The main deployment remains available with tests/security gates.
  Actions are pinned to commit SHAs, workflow permissions are read-only, and code
  quality checks no longer push automated changes to branches.
- Updated the dependency lock. Removed python-jose/ecdsa from the unused legacy
  auth middleware in favor of the PyJWT crypto dependency already used by the API.
  No known Python dependency vulnerabilities remain in the final pip-audit run.
- Added CI secret scanning, rejection of tracked env/key files and dependency
  auditing. These gates still need a hosted CI run; no remote deployment was made.

## Git history and Compose

Gitleaks v8.30.1 scanned 1,781 commits across local refs with zero detector findings.
A separate review of historical configuration found a fixed PostgreSQL password
in `docker-compose.yml` at commit `6b529d0c`, line 7. This low-entropy value was not
caught by Gitleaks. It looks like a default/example; whether it was ever used in
production is unknown. If used anywhere, rotate it. No secret values are reproduced
in this report. Deleting a file in a new commit does not remove its history.

There is no Compose file in the current backend checkout. The historical Compose
also mounted the whole repository into the backend and exposed port 8000 on all
interfaces. Do not reuse it as a production deployment template. Actual external
Compose files were not supplied and have not been inspected.

Do not rewrite shared history or force-push without coordinating with maintainers.
Credential rotation is required if any historical credential was actually used,
even if history is later rewritten.

## Validation

- 85 backend tests passed, including token/role authorization, privacy filtering,
  rate limits, local-only verification, CORS rejection and secret validation.
- pip-audit 2.10.1: no known vulnerabilities in the updated Python environment.
- Docker image built successfully; inspected by starting a network-isolated
  container: UID 10001, no `.env`, `.git`, local credentials, tests or development
  routes; application and Gunicorn worker import successfully.
- No cloud credentials, production secrets, real mail or production database were
  used or changed. No host/OS-package vulnerability scan or production network
  penetration test was performed; clean scans are not a guarantee of security.

## Required deployment actions

Set PostgreSQL/Redis/mail URLs and strong independent secrets through protected
runtime environment configuration. Set allowed frontend origins explicitly.
Rotate the historical database password if it was ever used. Restrict backend,
PostgreSQL and Redis ports to trusted private peers; expose the application through
HTTPS and a trusted reverse proxy/CDN. Configure proxy logging without query strings.
See `request-protection.md` for Redis, proxy trust and DDoS limitations. Keep the
base image and lockfile updated and review future scanner findings.
