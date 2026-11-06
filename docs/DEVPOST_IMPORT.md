# Devpost project import

Organizers export **Manage → Metrics → Projects data** in Devpost and upload the UTF-8 CSV in **Gestió → Event → Projectes i jurat → Devpost**. This is a reviewed CSV integration, not an undocumented Devpost API or a scraper.

## Submission form

Add custom questions for **HackEPS team code**, **Challenge**, and optional **MLH** (Yes/No). Participants use their existing HackEPS group code. Organizers can inspect codes in the Devpost tab. Do not match by project names, nicknames, or email addresses.

Export completed submissions only, or include a submission-status column. The importer accepts comma, semicolon, and tab delimiters, quoted fields/newlines, and a UTF-8 BOM. Limits: 1 MB in the UI, 1,000,000 characters server-side, 2,000 non-empty rows, 150 columns. Exported headers vary: column mapping is editable, with common English headers detected automatically. Select the exact complete-status values from your export; other statuses are visibly excluded. If the export omits statuses, explicitly confirm it excludes drafts.

Map each challenge value to a published challenge whose ID also names a configured room. MLH requires a room with ID `mlh`. Without an MLH column, no optional MLH presentation is requested.

## Review and import

1. Upload the CSV and select project URL, project title, team code, challenge, optional MLH, and status columns.
2. Preview, resolve unknown codes/challenges and duplicate rows, and preview again after changing mappings.
3. Enter a reason and import. Every eligible row must pass validation; writes are atomic.
4. Inspect the resulting projects and preserved-turn warnings. In **Presentacions**, generate the schedule using the existing scheduler and review capacity/conflicts.

New teams receive a challenge presentation and an optional MLH presentation. Import does not generate times automatically. Any team with existing presentations keeps all of its turns, states, rooms, positions, pins, and times. A changed imported challenge/MLH preference is recorded as project metadata and flagged for manual review; it does not silently rewrite queues. Manually enrolled teams and projects absent from subsequent files are preserved. This allows organizer exceptions; importing is not a deletion or reset operation.

A project URL is unique within an event, and each team has at most one imported project. Existing links cannot be reassigned through CSV. URLs must be HTTPS Devpost project URLs; the backend never requests them. The importer stores only project title/link, team relation, challenge and MLH preference, rather than the whole CSV or unrelated personal columns.

## API and audit

- `POST /v1/operations/{event_id}/devpost/preview`: CSV text, column mapping, challenge mapping, completed statuses or explicit completed-only confirmation. Returns per-row actions/errors/warnings and a digest.
- `POST /v1/operations/{event_id}/devpost/import`: same input plus `preview_digest`, UUID `operation_id`, and `reason`.
- `GET /v1/operations/{event_id}/devpost/projects`: imported project links for management.

All endpoints require a current admin/superadmin role. An event lock serializes imports with other operation writes. The preview digest detects changed input/configuration, team matching, project links and queue state. A stale preview returns 409. Retrying an identical confirmed operation returns its original result; reusing its UUID with another actor or payload returns 409. Reimporting with a new preview updates metadata without duplicate projects or presentations.

`devpost.import` audit entries record actor, time, filename, file SHA-256, reason, mappings, completion policy, project changes, queue decisions and counts. They do not retain the raw CSV. Deploy migration `20261106_devpost` before enabling the UI.

## Validation scope

Automated integration coverage uses the isolated PostgreSQL test database for CSV parsing, draft exclusion, custom mappings, duplicate/foreign/invalid rows, permissions, atomic rejection, replay, stale preview, preserved turns, audit and scheduler handoff. Use a real organizer export to confirm its headers and status values before the event.
