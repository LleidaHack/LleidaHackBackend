# Participant uploads and account timestamps

Profile image writes accept only base64 data URLs containing actual PNG, JPEG
or WebP images, at most 1 MiB decoded and 16 million pixels. URLs, SVG, animated
images, type mismatches and malformed images are rejected. Pillow decodes and
re-encodes only pixels so metadata and trailing payloads are not stored.

CV writes accept PDF only, at most 1 MiB and 20 pages. The parsed object graph
is inspected for JavaScript, active actions, embedded files and rich media;
encrypted and malformed PDFs are rejected. The stored PDF is rebuilt from
pages without annotations, document metadata or attachments. This is file
validation and sanitisation, not an antivirus or a guarantee against every
possible vulnerability in a PDF viewer. Keep the parsers updated.

These rules apply at request-schema validation for account creation, profile
updates, and event registration/update. Read schemas do not reinterpret legacy
values. Existing stored files are not retroactively sanitised. Deploy the
backend together with the frontend: browser restrictions alone can be bypassed.

The request body limit is 3 MiB so a profile request containing a 1 MiB image
and 1 MiB CV, with base64 overhead, can pass transport validation; each file
still has its own 1 MiB limit. Review any proxy or deployment override of
RATE_LIMIT__MAX_BODY_BYTES if large, valid uploads are rejected before the API.

New users receive a fresh UTC creation timestamp on each INSERT, rather than
the date captured when the module was imported. Profile responses include the
time and UTC offset. This fixes new records; dates already stored incorrectly
cannot be inferred or repaired without a trustworthy audit trail.
