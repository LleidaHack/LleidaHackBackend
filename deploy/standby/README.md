# Clouding standby preparation — NOT ACTIVATED

This is a staged recovery plan. Do not provision, change PostgreSQL settings,
redirect production, or promote any database until the user authorizes the rollout.
The current application can continue changing; pin both servers to the same
validated release when the infrastructure is activated.

## Inventory to complete at activation

- Clouding primary VPS: existing production host.
- Clouding standby VPS: not yet selected/provisioned. Prefer a separate host/failure
  domain; confirm placement options with Clouding rather than assuming isolation.
- Private connectivity: confirm private networking availability, otherwise use
  WireGuard. Never expose PostgreSQL or Redis publicly.
- Stable API ingress: choose an external health-aware entry point before cutover.
  A reverse proxy on the primary VPS alone does not survive that VPS failing.
- Monitoring destination and who is on call: to be configured.
- PostgreSQL: match the current major version and extensions; check disk capacity,
  WAL retention and actual database size first. Current production uses PostgreSQL 15.
- Runtime secrets, uploads/static mounts, TLS, CORS, image digests and connection
  limits must be inventoried. Replicating only the container image is insufficient.

## Staged rollout

1. Obtain and checksum an independent backup of application and mail databases,
   configuration and uploads. Restore into isolation and verify existing data.
2. Prepare the standby host, firewall and private connection. Initially allow only
   SSH administration and PostgreSQL from the primary's private address.
3. Create a narrowly scoped replication role on primary. Configure a physical
   replication slot with bounded WAL retention and alert before disk exhaustion.
   Use a private pgpass file, not passwords in commands or repository files.
4. Populate a NEW, empty standby volume using `pg_basebackup` with recovery
   configuration (`-R`). Never run it over an existing primary/data volume.
5. Start standby PostgreSQL and check `pg_is_in_recovery()` and WAL replay status.
   Run `check_replica.py` against both servers using private environment files.
6. Start the standby API against the SAME writable primary database. Keep background
   workers disabled there. Share signing keys and session dependencies; ensure Redis
   loss and local file storage do not leave hidden dependencies on the failed VPS.
7. Test moving API traffic only, while keeping the database primary unchanged.
8. Decide synchronous durability versus availability explicitly. Physical replication
   alone is asynchronous. For confirmed QR operations to wait for the standby, verify
   the named synchronous standby and `synchronous_commit` policy, then rehearse loss
   of either node. Do not silently fall back to asynchronous commits.
9. Rehearse whole-host failure with fictitious data before accepting the topology.

## Manual database failover runbook

A timeout is NOT proof that primary is dead. Never promote just because a health
probe fails. With two nodes there is no independent majority to decide ownership.

1. Pause writes and workers, record the last confirmed scan IDs, retain uncertain
   operation UUIDs on devices, and declare one operator responsible for recovery.
2. Fence the former primary through Clouding (power/network isolation). Record and
   independently verify that it cannot accept writes or restart automatically.
3. Confirm the standby's recovery state and replay position. With asynchronous
   replication, explicitly assess the potential data-loss window before proceeding.
4. Only after fencing, promote the selected standby with PostgreSQL `pg_promote()`.
   Verify it is writable and that the old primary remains fenced.
5. Point both APIs to the new primary. Start workers once on the new active host.
   Restore the API entry point, run readiness and authenticated read checks.
6. Retry uncertain QR operations using their ORIGINAL UUIDs, then verify audit,
   meals, wallets and presentation state. Never replay by generating fresh IDs.
7. Rebuild the old primary as a replica of the NEW primary. Never simply reconnect
   two writable database servers. Keep backups; application rollback must not
   restore an old database over new event activity.

No promotion or automatic failover script is supplied intentionally: until fencing
and ingress are concrete and tested, such automation would be unsafe. The preflight
script is read-only and does not change replication or database roles.

## Acceptance rehearsal

- Stop an API container: the other API serves QR operations with the same data.
- Disconnect primary VPS: fence it, perform guided failover, validate every
  acknowledged operation exactly once.
- Lose standby: observe the agreed synchronous write behavior; never show an
  uncommitted QR operation as confirmed.
- Drop a response after commit: replay original UUID and obtain the same result.
- Lose venue Wi-Fi: test organization's mobile fallback and scanner pending state.
- Keep Live countdown visible during disconnection; reconnect without restarting it.
- Verify recovery under expected peak load, then freeze infrastructure changes
  before the event. Record measured recovery times, not assumed guarantees.
