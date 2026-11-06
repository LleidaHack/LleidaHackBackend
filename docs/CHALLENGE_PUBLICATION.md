# Challenge publication boundary

Real challenges and preview decoys live in separate configuration collections:
`challenges` and `decoy_challenges`. Both support title, description, resources and
an individual `published` flag. Before global release, only published decoys are
returned by `/v1/operations/{event}/public` and `/challenges`. After release, only
published real challenges are returned. Neither endpoint accepts a private-mode
or release override from the caller.

Only admin/superadmin management routes can retrieve originals, drafts and the
configuration audit history. Only a superadmin can change `challenges_released`,
through either `/challenge-controls` or `/config`. Both paths use optimistic
versions and an event row lock and write an audit record. Admins can edit drafts
and decoys. Staff scanner permissions do not grant access to originals.

The public snapshot uses an explicit field allowlist. Adding a new management
configuration field does not publish it automatically. Decoy configuration,
internal notes and draft challenges are never copied into public responses.
Missing release flags are treated as false, including legacy configurations.
Deployment therefore hides legacy challenges until explicitly released by a
superadmin; there is no migration that silently publishes them.

Before release, room identifiers/titles and presentation data are hidden even if
the event phase is judging. Team choice endpoints return no real choices or
previous choice identifier, and participants cannot use enrollment to probe real
challenge IDs. Decoys cannot be selected as preliminary team choices. Existing
votes and presentation records remain intact and can be viewed by management.
All operations HTTP responses carry `Cache-Control: no-store, private, max-age=0`.

## Using Gestió

Open Projectes i jurat > Reptes. Save real challenges and decoys in their separate
editors. Mark the decoys intended for the preview as published. The global button
releases only the individually published originals and removes decoys from the
public response. Team voting remains a separate action after release.

## Boundaries

This protects data served by these API routes, not independently public files.
Keep unreleased resource files private at their storage provider; do not upload
secrets to a public bucket, public Git repository or public Devpost page. A URL
being omitted from an API response does not secure the destination. Do not copy
unreleased details into public activity titles, alerts, FAQs or maps.

Hiding a previously released challenge cannot retract information participants
already downloaded or recorded. Publish is a deliberate superadmin action.

## Validation

`tests/test_challenge_secrecy.py` covers anonymous users, hackers, scanner staff,
admin publication bypass attempts, missing flags, public query manipulation,
resource URL and identifier leakage, release/rehide and enrollment probing.
These run against the disposable `_test` database, not production or demo data.
