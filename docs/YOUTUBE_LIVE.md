# YouTube broadcasts on Live

The home page polls `GET /v1/operations/{event_id}/broadcast` every 30 seconds.
The backend resolves `@LleidaHack`, discovers public live videos and verifies that
embedding is allowed and the broadcast has actually started without ending.
A shared Redis cache and refresh lock prevent each participant or API worker from
consuming YouTube quota separately. Redis failure disables discovery.

Configure these backend environment variables and restart the API:

- `YOUTUBE_API_KEY`: a server-only Google API key with YouTube Data API v3 enabled.
  Restrict the key to that API and, where possible, the server IP. Never expose it
  through frontend environment variables or commit it.
- `YOUTUBE_CHANNEL_HANDLE`: defaults to `LleidaHack`.
- `YOUTUBE_DISCOVERY_SECONDS`: defaults to `900` (15 minutes), minimum 60 seconds.
  The standard search allowance is 100 requests/day. A shorter interval requires
  sufficient provider quota; 60 seconds can consume 1,440 searches/day.

Active broadcasts are checked every 30 seconds. New broadcasts can take up to the
configured discovery interval plus frontend polling time to appear. Requests are
made only while clients are polling. API failures hide the card and back off;
provider URLs containing credentials are never logged.

The large home-page player starts muted with autoplay requested. Browser settings
can still block playback; native YouTube controls and a direct link remain available.
The iframe stays mounted while the video ID is unchanged. No automatic audio is
requested. This does not start or publish a broadcast on YouTube.

Validation uses provider mocks. Real discovery and playback require a configured
API key and a public, embeddable live broadcast on the official channel.
