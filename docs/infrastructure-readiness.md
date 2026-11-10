# Infrastructure readiness and diagnostics

## Health and error correlation

`GET /health/live` checks the application process. `GET /health/ready` checks
PostgreSQL and Redis and returns 503 if a required dependency is unavailable.
Dependency errors and credentials are never included in the response. Database
connections enable pre-ping/recycling and bound pool waits/connect attempts to
five seconds; the readiness SQL statement has a 1.5 second statement timeout.
Redis checks use one-second connect/read timeouts.

Gestió now forwards the same generated `X-Request-ID` to the backend that it shows
as the failure reference. Backend logs include route templates (not raw URLs or
query credentials), status and duration for slow requests and 5xx responses.
Uncaught errors also log the reference without request bodies or credentials.
This helps attribute 502/504 failures; it does not establish that the previous
intermittent incident has been reproduced or permanently resolved.

After the backend release, run:

```bash
python3 deploy/health_probe.py https://backend.main.lleidahack.dev
```

Exit zero means healthy; nonzero means unavailable. Integrate this with the
existing monitoring system. The example `deploy/systemd/llh-readiness.*` units
run it every minute and record failures in the journal. Install the scripts under
`/opt/lleidahack` or adapt the unit path. The units are templates and have not been
installed on the VPS. Notification destinations must be configured in the chosen
monitoring system; no email or chat alert has been sent by this work.

## Restore rehearsal

Run from a backup machine with Docker and an independently recorded checksum:

```bash
python3 deploy/restore_rehearsal.py /private/backups/main.dump --sha256 <recorded-checksum>
```

The tool checks the checksum before starting Docker, creates a uniquely named
container with no network or published ports, restores the archive into a fresh
database, checks for public tables and removes only that temporary container.
No production database URL or password is accepted. Restore subprocess error
details are suppressed because SQL errors may contain participant data. Larger
archives may exceed the intentionally bounded 1 GiB temporary data filesystem;
review resource limits before increasing them. A restore failure is not evidence
that the production database is damaged.

Continue keeping off-host backups; this tool does not install a backup schedule.
Use the existing off-host gate documented in `production-deploy.md` before release.

## Bounded load rehearsal

```bash
python3 deploy/load_rehearsal.py http://127.0.0.1:8001 1 --clients 6 --rounds 10
```

Only loopback HTTP origins are accepted. The tool alternates readiness and public
Live snapshots at one request per second per client, with at most eight clients
and thirty rounds. It reports failures and p95/max latency. The automated event
rehearsal separately exercises authenticated mutations; neither proves venue
network or production capacity. Do not point stress tests at the live event.

## Existing mail delivery

Company invitations already use a persistent worker/outbox; participant resend
batches use individually bounded sequential requests with explicit ambiguous-send
handling. This release does not automatically retry uncertain email sends or
change their delivery state. Preserve that distinction when diagnosing the prior
38-recipient timeout: HTTP success/queued state is not proof of inbox delivery.
