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

## Badge-driven judging and optional MLH

Apply `20261106_judging_runtime` for actual presentation start/completion timestamps. The scanner's Presentation operation accepts a physical badge plus the selected room. One member identifies the event team; scanning another member of the currently presenting team is harmless. A new team's scan atomically closes the previous demo in that room, starts its own, and calls the next eligible team. All transitions share the event lock and the existing scan idempotency/audit mechanism. The last presentation can be closed through the management room controls.

Calls are refreshed across rooms after each successful transition. No team can be called/presenting in two rooms. MLH may call a completed team while it walks over, but its start scan enforces the configured travel buffer. Paused rooms, missing/ambiguous teams, wrong rooms, closed turns and unreleased judging are rejected. Scanner staff only receive room metadata once challenges are published and judging is open. Completed and postponed teams are not automatically recalled.

The schedule generator keeps one primary challenge plus the optional MLH enrollment. It compares five deterministic orderings, including primary-first, MLH-first, room-load and earliest-available strategies. It chooses the feasible result with the earliest overall finish, then the lowest sum of start times, while preserving pinned/active/closed turns and room/team/travel constraints. This is a bounded multistart heuristic, not a guarantee of the global optimum for every possible constraint set. It does not add MLH turns for teams that did not opt in or move challenge presentations to a different challenge's room. An overloaded challenge room therefore remains a real capacity limit; duration, judging window or room allocation must be adjusted by organisation.

Recalculation during judging starts pending turns no earlier than now. Impossible windows return an error without partially saving a schedule. Gestió shows each room's team count and estimated finish. Automated coverage includes an uneven 20/5 primary-room scenario with all 25 teams also at MLH: 10-minute demos and 5-minute travel finish in 250 minutes, matching the MLH capacity lower bound in that scenario. The Live projection shows the presenting team, called team and up to three more queued teams; the mobile queue exposes more entries.

## Meal-only mentors

Migration `20261106_event_mentors` activates the mentor model and adds an event-scoped mentor roster. The `mentor` access role is available to superadmins in user management. Existing accounts can be linked to an event after receiving that role; organisers can also create a name-only mentor record without issuing login credentials or an entrance ticket. The estimated 15 mentors is not a hard database limit.

Gestió > Event > Jornada > Meals provides the roster and activation controls. In the HackEPS scanner, staff select Mentor > Bind badge, choose the name and scan an unassigned badge. No ticket is required. Badge replacement requires admin/superadmin and revokes the previous code. Disabling a roster entry immediately blocks further meals for that event while preserving its history.

The existing voucher recipient column `hacker_id` is retained for API compatibility, but its foreign key now targets `my_user` so it can identify either a participant or a mentor. Existing participant assignments are preserved. Meal scans use the same per-person/per-round scan records, idempotency and audit; mentors do not enter the legacy hacker-only meal join table. Mentor badges reject activities, coin awards/redemptions, check-in and judging. Mentor accounts cannot enter management or scanner routes, and participant ticket generation excludes accounts with the mentor role. No mentor is added to a team, public leaderboard or event participant registration by this flow.

Downgrade refuses to remove the mentor schema while mentor identities/roles or non-hacker badge assignments remain; export/migrate those records first. This avoids silently deleting mentor history.
