# Nickname approval and badge-only scans

Apply migration `20261106_nicknames` before starting the updated API. It adds the nickname request history and a non-null `event_voucher.revoked` flag, defaulting to false for existing badges. No existing names, balances, check-ins or meal records are rewritten.

## Nicknames

All existing accounts must request nickname changes through `POST /v1/nicknames/me`. This policy is always enabled, including outside the event; there is no automatic end-date bypass. The current nickname stays public until an admin or superadmin approves it from Gestió > Users. The same screen shows pending requests and recent decisions. The user detail view allows direct corrections.

The API stores the user ID, previous/proposed names, request timestamp, decision, reviewer and resolution timestamp. Only one request per user can be pending. Approval checks availability again. Management corrections supersede pending requests. The legacy profile update helper rejects nickname changes, including requests from elevated accounts; corrections use the dedicated audited endpoint instead. Points and attendance remain associated with the existing user ID.

New proposals are normalized with NFKC and accept 2–40 letters, numbers, spaces, underscores, dots or hyphens. Availability checks are case-insensitive against current nicknames; the existing database unique constraint remains in place. Historic names are not rewritten and visually similar Unicode characters still require human moderation.

## Check-in and recovery

HackEPS > Organisation opens Check-in: scan the participant ticket, scan a free physical badge, then register. The existing voucher assignment transaction checks acceptance and registration, confirms assistance if necessary, records attendance and binds the badge. Duplicate assignments and cross-event badges are rejected.

Meal, activity and prize-redemption scans accept only assigned, non-revoked badges for the event, including the legacy meal route. A ticket cannot collect food or activity points. Management-only point awards/corrections can still identify a participant by ticket.

Admin/superadmin can choose Replace lost badge in the scanner: scan the original ticket and a new unassigned badge. Replacement uses the same event lock as scans and atomically revokes/unlinks the old badge, binds the new one and writes `badge.replace` with both badge IDs and the actor. Failed validation leaves the previous badge intact. An explicit unassignment also permanently revokes the badge. Revoked badges cannot be assigned again.

Attendance, meal rounds, activity participation and balances are keyed by participant ID, so replacement cannot reset them. The ticket remains available for organisation-assisted recovery. Legacy management attendance endpoints remain compatible; they do not make a ticket valid for meals or activities.

## Verification

API tests cover nickname permissions, legacy bypass, collisions, concurrent requests, approval/rejection history and corrections; badge tests cover ticket rejection, legacy meals, role restrictions, failed replacements, old-badge revocation and meal history across replacement. Browser checks cover profile requests, management rejection, mobile scanner layout and staff visibility. Physical camera scans and production deployment remain separate checks.

## Automatic judging waiting room

The public snapshot derives `phase=judging` when a configured hacking deadline expires. This does not mutate the stored phase or publish challenges. The client also switches at zero using server-corrected time, so the countdown disappears immediately while the next HTTP poll supplies the queues. Both home and fullscreen show the waiting room; unpublished challenges still suppress room and presentation data. Extending the deadline while the configured phase remains hacking restores the countdown. Explicit preparation/finished phases do not auto-transition; an explicit judging phase remains judging regardless of deadline changes.
