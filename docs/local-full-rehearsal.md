# Full local HackEPS rehearsal

This fixture only accepts PostgreSQL on localhost/127.0.0.1 with database name
`llh_operations_dev`. It never connects to production. The voucher CSV contains
only physical badge codes, not participant data or assignments. Keep that CSV and
generated artifacts outside Git. Codes remain independent from production after
import: resetting or assigning a local badge does not alter its real counterpart.

Before starting, preserve any previous local data with `pg_dump`. Initialize the
local database using `scripts/local-operations.sh` if it does not exist. Then:

```bash
uv run --env-file .env.operations.local python scripts/seed_full_rehearsal.py \
  --vouchers /private/path/vouchers_event_5.csv --output /private/path/rehearsal
```

Existing rehearsal data is preserved on rerun. Conflicting voucher codes abort the
import rather than reassign another event's badges. The older demonstration event
also remains intact. The new event has a later end date and is selected as the
current HackEPS by the existing API's calendar-year selection.

Use local API 8000, HackEPS 3001, Live 3000, Gestió 5175. Do not run delivery workers.
Set local mail URL to `http://127.0.0.1:59999/` with no mail server, and explicitly
blank Discord and VAPID configuration in the local environment. This intentionally
prevents real mail, Discord and push delivery; account/registration behavior can
be exercised but mail sending itself is not part of this rehearsal.

Accounts share the LOCAL-ONLY password `LocalDemo2026!`:

- `organizer@example.test`: superadmin; `admin@example.test`: management.
- `lleidahacker@example.test`: continuous QR scanner.
- `participant01@hackeps.test` through `participant40@hackeps.test`.
- `mentor01@hackeps.test` and `mentor02@hackeps.test`.
- `rodi@hackeps.test`, `vallcompanys@hackeps.test`, `openfort@hackeps.test`,
  `jetbrains@hackeps.test`, `paeria@hackeps.test`: shared company portal accounts.

Participants 01-36 are accepted/confirmed, 37-38 accepted/unconfirmed and 39-40
pending acceptance. All start without check-in or assigned badges. Participants
01-06 have dietary restrictions. Ten teams, five challenge/company rooms plus MLH,
three meals, a workshop, prizes and example projects are ready.

## Suggested test order

1. Open generated `tickets.html` on a second screen or print it. On the scanner,
   select accreditation, scan a fictitious ticket and then a REAL printed badge.
2. Check the profile/check-in count. Scan a meal twice: the duplicate must be
   rejected. Use participants 01-06 to exercise dietary notices.
3. Test awards, redemption and voucher reset. Resetting locally must clear the
   check-in/meal state and allow accreditation again; production stays untouched.
4. Open the company portal. It selects the current event and assigned room.
5. In Gestió, change Live phase from hacking to judging when ready. The deadline
   is 24 hours ahead; judging hours allow the next three days.
6. Select judging and the correct room on the scanner. Scan an accredited team
   member. Company starts five minutes, extends and finishes. Test next-team calls.
7. Compare projects and save notes. Close the company evaluation only after its
   turns are done/absent. Test management reopening and incident resolution.
8. Briefly disable network in browser devtools and verify pending/retry behavior.

The HTML is a collection of fictitious admission tickets, not a public export of
physical voucher codes. Use desktop localhost for camera access. Phone testing
requires a separately prepared secure local origin; localhost on a phone refers
to the phone, not the computer. Do not expose this rehearsal publicly by default.
