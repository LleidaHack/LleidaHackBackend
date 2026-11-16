# Google Wallet event tickets

Apple email buttons download the pass directly. The Google endpoint checks the same
current event eligibility as QR and Apple downloads, creates one event class and one
object per existing user code, and redirects to Google's save flow. Users confirm
adding the pass in their wallet. No new QR or physical badge identity is generated.

## Activation

1. Create a Google Wallet API issuer account in Google Pay & Wallet Console.
2. Enable Google Wallet API in a Google Cloud project. Create a service account and
   grant that account Developer access in the Wallet issuer console.
3. Obtain a JSON service-account key and store it as a mounted server secret, outside
   the repository. Set `GOOGLE_WALLET_CREDENTIALS_PATH` to its container path and
   `GOOGLE_WALLET_ISSUER_ID` to the numeric issuer ID.
4. In demo mode, add test Google accounts in the issuer console. Enable
   `GOOGLE_WALLET_ENABLED=true` only for testing with those accounts. The credentials
   must also be present in the mail-dispatch backend process; it selects the
   six-field `event_attendee_ticket_wallets` template when enabled.
5. Test adding a real eligible ticket on Android, then request publishing access in
   the console before enabling for all attendees. Until then keep production
   `GOOGLE_WALLET_ENABLED=false` so neither the website nor emails advertise it.

Deploy the MailBackend migration first (new template), then backend and frontend.
Publish the versioned email badges and backend `static/images/wallet/google-*.png`
assets in their public static mounts. The browser route is
`/entrada/{event_id}/{code}/google-wallet`; credentials never reach the frontend.
OAuth and save tokens are signed with RS256; the save token references a stored
object to stay below Google's recommended 1800-character limit. API failures return
503 with no credential or Google response content exposed.

Existing objects are reused and current name/role/QR data is refreshed on access.
This integration does not push revocations to passes that users have already saved.

Docs: https://developers.google.com/wallet/tickets/events/web

## Prepared production activation (pending Google approval)

`deploy/compose-google-wallet.production.yml` contains the production configuration
change. It is **not loaded automatically**: merging this file does not enable
Google Wallet, and the application default and `.env.example` remain disabled.
Do not apply it while the issuer's publishing request is under review.

Preparation completed on 2026-11-16:

- Backend, frontend routes, public image assets and the two-wallet mail template
  have been deployed.
- The production issuer is `3388000000023228427` (LleidaHack). The service account
  is `lleidahack-wallet@hackeps2026.iam.gserviceaccount.com`; the JSON key is stored
  outside the repository and mounted read-only at
  `/run/secrets/google-wallet/service-account.json`.
- Dedicated demo passes use the event title **HackEPS 2026** and Hacker, Mentor
  and Staff roles. Their QR values are synthetic and cannot check in attendees.
- The three demo objects, their roles, QR payloads and signed save links were
  verified against Google's API. An organizer confirmed saving a demo pass on
  Android and that it displays correctly. This does not verify a real attendee's
  profile/badge QR or prove public publishing access.

### Release procedure after approval

1. Confirm the issuer console explicitly grants publishing access. Demo saves
   working is not sufficient.
2. Back up the current production Compose configuration. Merge the three
   environment overrides from `deploy/compose-google-wallet.production.yml` into
   the canonical `/root/LleidaHackWeb/docker-compose.yml`, preserving the existing
   images, other environment values, volumes, networks and secrets. Persist the
   changes in that canonical configuration so subsequent releases retain them.
3. Validate the resulting configuration with `docker compose config --quiet`
   using the existing project directory, project name and `main` profile. Check
   that the issuer ID, credentials path and readable secret mount remain present
   on all three services. Do not print the credentials or resolved environment.
4. Recreate only `backend-main`, `backend-push-worker-main` and
   `backend-company-mail-worker-main` using the existing production deployment
   procedure. No database migration or mail-service restart is needed for this
   configuration change. Check API health and worker status.
5. With one authorized eligible test recipient, verify the profile's Google
   Wallet button and `/entrada/{event_id}/{code}/google-wallet` save flow. Check
   that the barcode equals that recipient's existing profile QR and that the
   intended event name and role appear. The production title comes from the
   event record; the demo title does not rename the real event.
6. From Communication, explicitly select that one recipient before sending a
   test invitation. Confirm both wallet buttons work from the email and that
   the Google pass has the same QR as the profile. Do not start a bulk send as
   part of activation. Participants still require acceptance and confirmed
   attendance; mentors and staff retain their existing eligibility rules.

### Rollback

Set `GOOGLE_WALLET_ENABLED` back to `"false"` on those same three services in the
canonical Compose configuration and recreate them. The profile and newly sent
emails stop offering Google Wallet; existing Google links return unavailable.
Apple Wallet remains enabled. Previously saved Google passes are not revoked by
this switch. No database restore or credential deletion is required.
