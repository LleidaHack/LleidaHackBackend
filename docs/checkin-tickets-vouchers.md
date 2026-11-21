# Check-in tickets and vouchers

Flow for an edition, from closed registrations to meals during the event.

1. **Tickets.** In llh-admin → Comunicació, review recipients and choose all,
   confirmed participants, active mentors, or staff. `POST /v1/event/{id}/tickets/send`
   accepts `audience=all|hacker|mentor|staff`; `force=true` resends that audience.
   Participants must be accepted **and confirmed**. Mentors must be active in the
   event roster. All non-deleted accounts with `lleidahacker`, `admin`, or
   `superadmin` roles are staff, as requested; they need no participant registration.
   Missing-email recipients are shown but not sent mail. The background job sends
   `event_attendee_ticket`, with fields `name,event_name,role,code,qr_url,ticket_url`.
   Values are HTML escaped and commas encoded to preserve positional fields.
   `GET /v1/event/{id}/tickets/status` returns totals, per-role groups, and a
   management-only recipient preview. Delivery history remains in hacker registration
   rows for existing participants; mentors/staff use `event_ticket_delivery`.
2. **Personal entry.** The email embeds `GET /v1/event/{id}/ticket/{code}/qr.png`
   and links to `/ticket/{code}/view`. The latter displays the QR and offers Apple
   Wallet when configured, without requiring a login. All downloads check current
   role/membership, reject deleted identities, and reuse the user's existing code.
   Mentor invitation contacts can be entered or edited in the event's Mentors tab
   or supplied as an optional `email` CSV column. They do not change login identity.
   Changing a contact resets that mentor's delivery status for this event.
3. **Vouchers.** Physical badges printed before the event. An organizer
   generates them with `POST /v1/event/{id}/vouchers/generate` (`{"count": N}`)
   and downloads `GET /v1/event/{id}/vouchers/export.csv` for the print shop.
   Codes look like `V7KQ4M2XH` (9 chars, unambiguous alphabet, no separators so
   scanners that strip punctuation keep them intact; can be typed by hand);
   `GET /v1/event/{id}/vouchers/{code}/qr.png` renders one.
4. **Check-in.** The llh-checkin app scans the hacker's ticket, then a blank
   voucher, and calls `PUT /v1/event/{id}/vouchers/{voucher_code}/assign/{hacker_code}`.
   This marks participation (forcing confirmation if needed) and binds the
   voucher to the hacker in one transaction. Active mentors and staff can also
   bind their user-code ticket to a voucher, without a hacker registration or
   participation record. A voucher can be assigned once and
   a hacker can hold one voucher per event; `DELETE …/vouchers/{code}/assign`
   releases a lost badge (participation is kept).
5. **During the event.** Any endpoint that takes a hacker code
   (`PUT /v1/meal/{id}/eat/{code}`, `GET /v1/user/code/{code}`,
   `PUT /v1/event/{id}/participate/{code}`) also accepts an assigned voucher
   code, so meals are scanned against the badge.

`GET /v1/event/{id}/ticket/{hacker_id}` returns the ticket state for the
profile page (accepted, confirmed, `qr_url`, checked in, voucher code).

## Deploy order

The mail client loads every `InternalTemplate` at start-up, so the MailBackend
must have the new `event_attendee_ticket` template **before** this backend version
is deployed. Deploy MailBackend and its `20261116_attendee_ticket` migration first,
then run the backend `20261116_ticket_delivery` migration (mentor contact column
and staff/mentor delivery table), deploy the backend, then the admin and profile. `BACK_URL` must be the public backend URL: it is embedded in the mail
as the QR image source.

## Apple Wallet

The optional `apple_wallet_url` in ticket state downloads
`GET /v1/event/{id}/ticket/{code}/apple.pkpass`. Like the mail QR, this is a
bearer-code URL with the same participant/mentor/staff eligibility as the mail.
Treat the URL as private and redact ticket paths in proxy/access logs.
The barcode contains the existing `hacker.code`, exactly as the profile and mail;
it does not contain a URL, a new code, or the physical voucher code. Badge
assignment and meal scans therefore retain the existing behavior.

Mount these secret files outside static directories and the repository, readable
only by the backend service account, and configure:

- `APPLE_WALLET_P12_PATH`: exported certificate with private key.
- `APPLE_WALLET_PASSWORD_FILE`: UTF-8 password file (optional trailing newline).
- `APPLE_WALLET_WWDR_PATH`: Apple WWDR intermediate certificate matching the
  issuer of the pass certificate, downloaded from Apple's certificate authority.
- `APPLE_WALLET_TEAM_ID=5F659SC689`
- `APPLE_WALLET_PASS_TYPE_ID=pass.cat.lleidahack.tickets`

`BACK_URL` must be the public HTTPS backend origin. Empty configuration suppresses
Wallet links. Downloads return `503` when disabled or signing fails; neither key
material nor password is logged. The service validates the certificate identity,
validity and intermediate issuer before signing. Renew the signing certificate
before expiry. Wallet signing itself requires no schema changes; invitation
contacts and delivery tracking require the migration above.

Wallet is available from the participant profile and the personal email link.
Google Wallet and automatic updates/revocation of saved passes are not implemented.
The existing four-field ticket and six-field reminder templates remain unchanged.
A downloaded pass is not proof of current eligibility: check-in must continue
validating the code on the server. Test installation and scanning on a real iPhone
before enabling production. The sample signing tests use disposable certificates:
`python -m unittest tests/test_apple_wallet.py`.

### Wallet visual identity

The pass uses the approved email identity from
[MailBackend PR #40](https://github.com/LleidaHack/MailBackend/pull/40), source
commit `e83692459960763b2d5fa6fef0dd51761dadfe42`: charcoal `#2e2e2e`, warm white
`#f7f5ef`, orange `#ff7430`, peach labels `#ffb48c`, and sky blue `#97cef2`.
The original logo and cloud PNGs are bundled in `static/images/wallet/hackeps-2026`;
no cross-service image requests are required. The generator composes the event
strip at 375×98 points and includes 1x/2x/3x variants. The event name is a native
header field so it does not overlap the illustrated strip. Participant, date,
location and QR remain native PassKit content; Apple's typography is retained.
This artwork identifies the 10th edition; update it for later editions.

The masthead uses `logo_lleidahack_blanc.png` instead of `logoText`. A native
right-aligned `ROL` field appears next to the participant name: hacker → Hacker,
mentor → Mentor, and lleidahacker/admin/superadmin → Staff (legacy lleida_hacker
also maps to Staff). Unknown roles fail signing rather than receiving a guessed
label. Download eligibility is always checked independently against current
account role and event membership. Never use the printed role as authorization.

## Application rejection emails

The admin's individual, bulk and group rejection actions use
`event_hacker_rejected` with `name,event_name` (HTML-escaped, including commas).
Delivery is requested after committing the rejection. Individual repeat
rejections are rejected; group requests skip accepted and already-rejected
members, so repeating the action does not create another notification.

Deploy MailBackend with migration `20261120_hacker_rejected` before this backend:
its mail client loads all registered internal templates during initialization.
The mail subject is `Sobre la teva inscripció · HackEPS`.

Withdrawing acceptance (`PUT /v1/event/{event_id}/unaccept/{hacker_id}`) also
marks the applicant rejected and sends the same rejection email after commit.
It clears attendance confirmation and its token, so the old confirmation link
and ticket are no longer eligible. Repeated withdrawal does not send another mail.
