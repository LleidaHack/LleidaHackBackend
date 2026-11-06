# Official Discord announcements

## Incoming webhook (recommended)

Configure `DISCORD_WEBHOOK_URL` and `DISCORD_WEBHOOK_EVENT_ID` in the backend secret
environment. The URL must be an incoming `https://discord.com/api/webhooks/...`
webhook. It is never returned by the API, stored in audit records or committed.
Restart the API after changing these values and run a separate worker with the
same database and environment:

```sh
uv run --env-file .env.operations.local python -m src.impl.Operations.discord_worker
```

For a server deployment, supervise this command as a separate service/container.
Keep one configured event per worker. An event-specific PostgreSQL advisory lock
serializes webhook sends across worker instances; do not point different events
at the same webhook. A configured webhook takes precedence over bot claim/ack so
two transports cannot consume the same queue.

In Gestió, open Comunicació > Avisos, select Discord and enable the card format.
The alert title and message become the embed title and description. Optional
fields include a hex color, HTTPS title link, image, thumbnail, footer and up to
five custom fields. A visual preview is shown before publishing. Disable the card
for plain text. URL/title/field length validation keeps the payload below Discord
limits. `allowed_mentions.parse` is always empty, including for plain text.
The UI preview displays text literally; Discord interprets supported Markdown.

The worker requests `wait=true` and stores Discord's message ID only after a
successful response. Delivery status remains pending until processed. Expired or
cancelled alerts are not sent. Rate limits honor `retry_after`, delaying the entire
event queue. Connection failures and 5xx responses retry with backoff, up to five
attempts. Permanent failures stop. Ambiguous timeouts fail with a request to check
the channel before resending, rather than blindly posting duplicate announcements.
No remote response bodies or token-bearing URLs are written to delivery errors.

An unavoidable crash after Discord accepts a message but before the database
commit can still duplicate a delivery on restart. Webhook posting has no
transaction shared with our database. Withdrawing an alert cancels pending work;
it does not delete a message already sent to Discord. Alert expiry controls queue
eligibility, not message deletion in Discord.

Automated tests use mocked HTTP responses and a disposable test database. A real
webhook GET validates configuration without publishing a message. Sending a real
announcement is performed explicitly with the Publish button.

## Optional external bot contract

The pull/ack contract remains available when no webhook is configured for the
event. The bot is a separate application; the backend provides its queue.

Configure server-side environment variables:

- `DISCORD_BOT_SHARED_SECRET`: a random secret of at least 32 bytes, also held by the bot. This is not the Discord bot token and grants no user-management access.
- `DISCORD_BOT_EVENT_ID`: the one event that this connector may consume.
- `DISCORD_CHANNEL_ID`: the official Discord channel snowflake as a string.

The bot keeps its Discord token in its own secret store. Do not expose either token in a browser, URL, client build or logs. Backend endpoints are restricted to the configured event and require `X-Discord-Bot-Key`.

1. Poll `POST /v1/operations/{event_id}/discord/claim` every few seconds. The JSON array contains up to 20 deliveries: `id`, `alert_id`, `lease_token`, `lease_until`, `channel_id`, `message`.
2. Persist a mapping from `alert_id` to the Discord message ID in the bot. Reconcile retries with that mapping before posting. Preserve `message.allowed_mentions = {"parse": []}` to prevent organizer text from pinging everyone or roles. Plain content is capped at 2,000 characters; card messages use the same validated embed formatter as webhook delivery.
3. Post to the returned channel using the bot's Discord client. Respect Discord rate limits and finish within the two-minute lease.
4. Acknowledge with `POST /v1/operations/{event_id}/discord/{id}/ack` and JSON `{"lease_token":"...","message_id":"123456789"}`. Repeating a successful acknowledgement is safe.
5. For a transient failure, acknowledge `{"lease_token":"...","error":"Safe short failure description"}`. Never include tokens or raw sensitive response bodies. The backend requeues until five attempts. Lost leases can be reclaimed after two minutes; stale lease tokens cannot acknowledge another worker's delivery. Alerts that expire before claim are not sent.

Delivery is at-least-once. A crash between posting to Discord and saving/acknowledging the message can duplicate a post unless the bot reconciles it. Withdrawing an alert cancels uncompleted work, but cannot retract a post already made or reliably stop a bot already publishing. Sent messages remain visible in the audit/status view by their Discord message ID.

Authenticated admins and superadmins can inspect `/v1/operations/{event_id}/discord-deliveries`; staff scanners and participants cannot. Shared bot credentials only authorize claim/ack, never management or coin endpoints. The queue and its status are migrated in `20261105_discord_outbox`.
