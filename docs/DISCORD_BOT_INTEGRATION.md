# Official Discord bot alert contract

The bot is a separate future application. This backend supplies a persistent pull/ack queue; it does not pretend to send messages before a bot exists. Staff select Discord when publishing an alert in Gestió. Nothing is sent externally by this repository alone.

Configure server-side environment variables:

- `DISCORD_BOT_SHARED_SECRET`: a random secret of at least 32 bytes, also held by the bot. This is not the Discord bot token and grants no user-management access.
- `DISCORD_BOT_EVENT_ID`: the one event that this connector may consume.
- `DISCORD_CHANNEL_ID`: the official Discord channel snowflake as a string.

The bot keeps its Discord token in its own secret store. Do not expose either token in a browser, URL, client build or logs. Backend endpoints are restricted to the configured event and require `X-Discord-Bot-Key`.

1. Poll `POST /v1/operations/{event_id}/discord/claim` every few seconds. The JSON array contains up to 20 deliveries: `id`, `alert_id`, `lease_token`, `lease_until`, `channel_id`, `message`.
2. Persist a mapping from `alert_id` to the Discord message ID in the bot. Reconcile retries with that mapping before posting. Preserve `message.allowed_mentions = {"parse": []}` to prevent organizer text from pinging everyone or roles. Content is capped at 2,000 characters.
3. Post to the returned channel using the bot's Discord client. Respect Discord rate limits and finish within the two-minute lease.
4. Acknowledge with `POST /v1/operations/{event_id}/discord/{id}/ack` and JSON `{"lease_token":"...","message_id":"123456789"}`. Repeating a successful acknowledgement is safe.
5. For a transient failure, acknowledge `{"lease_token":"...","error":"Safe short failure description"}`. Never include tokens or raw sensitive response bodies. The backend requeues until five attempts. Lost leases can be reclaimed after two minutes; stale lease tokens cannot acknowledge another worker's delivery. Alerts that expire before claim are not sent.

Delivery is at-least-once. A crash between posting to Discord and saving/acknowledging the message can duplicate a post unless the bot reconciles it. Withdrawing an alert cancels uncompleted work, but cannot retract a post already made or reliably stop a bot already publishing. Sent messages remain visible in the audit/status view by their Discord message ID.

Authenticated admins and superadmins can inspect `/v1/operations/{event_id}/discord-deliveries`; staff scanners and participants cannot. Shared bot credentials only authorize claim/ack, never management or coin endpoints. The queue and its status are migrated in `20261105_discord_outbox`.
