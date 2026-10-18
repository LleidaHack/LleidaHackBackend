# One-command production deployment

This command deploys the latest fetched `main` commit to `backend-main` on the
LleidaHack VPS. It never merges a pull request. Only run it when you intend to
activate the latest validated production release.

## One-time setup after merging this change

The VPS already has Docker Compose, Python 3, PyYAML and the repository checkout.
Run as root:

```bash
cd /root/LleidaHackWeb/releases/backend/preparation-source
git status --short  # Must be empty; preserve any local edits before continuing.
git fetch origin main
git checkout --detach origin/main
# Create only if this path does not already exist; inspect an existing launcher.
ln -s /root/LleidaHackWeb/releases/backend/preparation-source/deploy.sh /root/LleidaHackWeb/deploy.sh
```

## Routine use

```bash
cd /root/LleidaHackWeb
./deploy.sh --check  # Optional: preflight only.
./deploy.sh          # Build, back up, activate and verify.
```

`--check` fetches Git metadata and reads CI/host state. It does not change the
checkout, build an image, back up the database or restart services. If the latest
commit is already running, a normal invocation also exits without restarting.
The resolved SHA is fixed for the run; a later merge is left for the next run.

## Safety gates

- Exclusive host lock shared with the existing candidate-preparation workflow.
- Clean checkout, expected GitHub origin, healthy current backend and known image
  revision. Current image must be an ancestor of the target commit.
- Latest push-to-main validation run for the exact SHA must succeed, including
  the backend tests and repository security jobs. Pending, failed or unavailable
  CI blocks deployment. Public GitHub API access normally needs no credentials;
  `GH_TOKEN` can be supplied privately if API rate limits require it.
- Any changes under `alembic/` or to `alembic.ini` block deployment. Migrations
  require a separate reviewed release with a write freeze and preservation
  verification. There is intentionally no `--force` bypass.
- Production Compose must use the expected migration-free Gunicorn command,
  immutable image and healthcheck. Runtime settings must match the live backend.
- At least 2 GiB free disk space before building. Immutable candidate imports are
  checked without network or production credentials.
- Fresh custom-format PostgreSQL backup, archive table-of-contents validation,
  private configuration backup and SHA-256 checksums before activation. Archive
  validation is not a full restore rehearsal. Backups are mode-restricted and
  contain secrets and personal data; do not upload them to GitHub.
- Only the backend image is changed. Databases, volumes, mail, Redis, environment
  values and static-file mounts are retained. Runtime/configuration drift during
  preparation stops the deployment.
- Docker health, public HTTPS, anonymous auth rejection, authenticated event
  reads and the mail connection are checked. No test users or emails are created.

There is a brief interruption while Docker recreates the single backend
container. This is not a zero-downtime rolling deployment.

## Off-host backups

The default backup is stored on the VPS under `/root/backups/deploy-<timestamp>`.
A same-host backup does not protect against loss of the VPS. To require a copy to
an existing off-host location before every cutover, create this private file:

```text
/root/LleidaHackWeb/deploy-backup-destination
```

Its single line is an SCP destination such as `backupuser@backup-host:/private/llh/`.
Set permissions to `600`. Configure SSH key authentication and verify the host
key beforehand. SCP runs in batch mode: if copying fails, deployment stops before
changing the application. No credentials belong in the destination string.
Without this file, arrange an independent off-host backup process or copy the
reported backup directory manually. Existing daily backups remain unchanged.

## Recovery

Failed activation/health/smoke checks restore the previous Compose configuration
and restart only the old backend image. The previous image must remain on disk.
Database dumps are **never** automatically restored: new user activity must not
be discarded. A second verification failure is reported as an automatic rollback
failure and requires immediate investigation.

External Compose edits are never overwritten during recovery. The lock only
coordinates this tool and workflows using the same lock; avoid running other
Docker/Compose deployment commands concurrently. An uncatchable termination
(`kill -9`, power failure) cannot run automatic recovery.

If recovery is required manually, identify the backup directory printed by the
command, review that its configuration is still applicable, then:

```bash
cd /root/LleidaHackWeb
cp /root/backups/deploy-<timestamp>/compose-before.yml docker-compose.yml
docker compose -p lleidahackweb --profile main up -d --no-deps --no-build backend-main
docker inspect backend-main --format '{{.State.Health.Status}}'
```

Do not use `down -v`, remove database volumes, or restore an old dump over live
production as an application rollback.
