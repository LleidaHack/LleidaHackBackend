# Event operations readiness

## Organizer workflow

Gestió opens an event on **Estat de l’esdeveniment**. The view refreshes every
15 seconds while visible and on window focus. It reports accepted and confirmed
expected attendees, checked-in attendees, remaining expected check-ins, meal
counts, declared dietary answers, room activity, incidents and recent rejected
operations. Dietary responses are raw declarations, not medical classifications.
Counts are scoped to the selected event. Private status is restricted to admins.

Create an incident with a title and details, then resolve or reopen it. Repeated
creation with the same operation ID is idempotent; status updates reject stale
versions. Creation and resolution are recorded in the operations audit.

The room pause button blocks new admissions/timer starts but does not terminate
an active presentation. Resume it after resolving the issue. Judging rows offer
mark absent, return to the back of the queue, and move to the selected room.
All recovery requires a reason, records an audit entry, refreshes preparation
calls, and rejects stale versions. An active presentation must be finished before
recovery; moving a completed presentation is rejected. Existing detailed editing
and superadmin overrides remain available.

## Company decision

Companies compare projects and propose a winner as before. After all their room
presentations are done or absent, they can confirm the winner and close the
evaluation. This locks notes and winner edits across devices; results remain
private. Only management can reopen the evaluation with a recorded reason.
Note changes advance the decision version so a stale confirmation cannot silently
close over a newer evaluation. Retried closure uses its original operation ID.

## Scanner connection recovery

Offline devices stop registering new scans. An uncertain scan retains its exact
operation ID, payload and form in session storage before transmission. Reloading
the same tab restores the pending scan and blocks new ones until explicit retry.
A successful/rejected response removes it; signing out clears pending local scans.
The original UUID allows the backend to replay a committed result without applying
meals or coin movements twice. This is not offline admission: do not distribute
benefits before confirmation. Closing the tab or losing browser storage does not
preserve the pending command; consult the audit before rescanning in that case.
Badge assignment recovery retains the existing explicit acknowledgement workflow.

## Local rehearsal and evidence

`uv run pytest tests/test_event_readiness.py` exercises registration/acceptance,
badge admission, meal service, dashboard counts, incident resolution, QR room
admission, company timer start/extension/finish, notes, winner confirmation and
admin reopening. It uses the isolated `_test` database and sends no real email.
The separate judging recovery case checks authorization, stale updates, pause,
requeue and refusal to move an active team.

The Nov 9 production backup `main-final.dump` was restored on Nov 10 into a
network-isolated disposable PostgreSQL container: its recorded SHA-256 matched
and 46 public tables were recovered. This establishes that this particular backup
restores, not that future backups will. No production connection or data rewrite
was made. The temporary container was removed after verification.

A local single-process API candidate handled 60 read-only requests from six
simulated clients with zero failures, p95 74 ms and maximum 90 ms. This is a bounded
smoke test with demo data, not a production capacity guarantee. Physical camera,
vibration, venue Wi-Fi and full event concurrency still need a device rehearsal.

## Release order and rollback

Back up and verify production data before activation. This change follows
`20261109_company_timer` and adds migration `20261110_event_readiness`: a nullable
company decision timestamp and a separate incident table. Apply backend schema
and code before releasing Gestió and Live. The normal deployment script correctly
refuses migrations; use the documented reviewed migration procedure. Keep the
existing records and additive schema when rolling back application images; do not
restore an older database over new event activity. No release was activated by
this implementation task.
