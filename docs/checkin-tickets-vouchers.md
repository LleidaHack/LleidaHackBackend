# Check-in tickets and vouchers

Flow for an edition, from closed registrations to meals during the event.

1. **Tickets.** Once registrations are closed and hackers are accepted and have
   confirmed, an organizer presses *Generate event tickets* in llh-admin →
   `POST /v1/event/{id}/tickets/send`. The job runs in background and mails the
   `event_hacker_ticket` template to every accepted **and confirmed** hacker that
   has not received it yet (`?force=true` resends to all of them).
   The ticket QR encodes the hacker's user `code`; the same QR is shown on the
   hackeps profile. Progress: `GET /v1/event/{id}/tickets/status` (counts come
   from `hacker_event_registration.ticket_sent_at`, so it is safe with several
   gunicorn workers).
2. **QR image in the mail.** The mail backend cannot attach files or inline
   images, so the template embeds `GET /v1/event/{id}/ticket/{code}/qr.png`.
   The endpoint is public (mail clients cannot authenticate) but only renders a
   QR for hackers accepted and confirmed for that event; the code is a random
   20-letter string.
3. **Vouchers.** Physical badges printed before the event. An organizer
   generates them with `POST /v1/event/{id}/vouchers/generate` (`{"count": N}`)
   and downloads `GET /v1/event/{id}/vouchers/export.csv` for the print shop.
   Codes look like `V7KQ4M2XH` (9 chars, unambiguous alphabet, no separators so
   scanners that strip punctuation keep them intact; can be typed by hand);
   `GET /v1/event/{id}/vouchers/{code}/qr.png` renders one.
4. **Check-in.** The llh-checkin app scans the hacker's ticket, then a blank
   voucher, and calls `PUT /v1/event/{id}/vouchers/{voucher_code}/assign/{hacker_code}`.
   This marks participation (forcing confirmation if needed) and binds the
   voucher to the hacker in one transaction. A voucher can be assigned once and
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
must have the `event_hacker_ticket` template **before** this backend version is
deployed. `BACK_URL` must be the public backend URL: it is embedded in the mail
as the QR image source.
