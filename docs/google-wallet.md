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
