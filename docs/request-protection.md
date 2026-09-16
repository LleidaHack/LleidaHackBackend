# Request protection

The application limiter is enabled by default and runs before database sessions
and endpoint logic. Redis is required; all workers/replicas must use the same
Redis instance, prefix and signing secret. No in-memory fallback exists.

## Defaults

| Scope | Budget | Setting under `RATE_LIMIT__` |
| --- | --- | --- |
| All HTTP requests, per IP | 30/second and 300/minute | `BURST_PER_SECOND`, `REQUESTS_PER_MINUTE` |
| Login, per IP | 20/minute | `LOGIN_PER_MINUTE` |
| Login, per normalized account | 10/15 minutes | `LOGIN_PER_ACCOUNT` |
| Signup, per IP across all account types | 10/hour | `SIGNUP_PER_HOUR` |
| Password recovery, verification resend, contact, per IP | 20/hour combined | `MAIL_PER_HOUR` |
| Signup and public mail routes, per normalized email | 3/15 minutes combined | `MAIL_PER_RECIPIENT` |
| Signup and public mail routes, across all clients | 300/hour combined | `MAIL_TOTAL_PER_HOUR` |
| Request body | 1 MiB, including streamed requests | `MAX_BODY_BYTES` |
| Receiving the complete request body | 10 seconds | `BODY_TIMEOUT_SECONDS` |

Budgets count attempts, including invalid credentials/payloads; not just successful
operations. Contact emails identify the submitter, not the actual inbox recipient.
The global mail-route budget bounds public email abuse, not organizer bulk mail.
Account quotas can temporarily block legitimate login after malicious attempts;
IP limits may affect people sharing campus Wi-Fi. Tune these values for event
traffic and monitor 429s before opening registration. There is no permanent lockout.

Counters use atomic Redis Lua operations with expiry from the first request.
Rejected attempts do not renew expiry. IPs and normalized account names are stored
as HMAC digests, never raw email addresses or passwords. IPv6 addresses share a /64
quota. Rotating the signing secret resets identities; restarting Redis resets quotas.

Exhaustion returns JSON HTTP 429 with `Retry-After` seconds and `Cache-Control:
no-store`. Redis failure returns 503 with a short retry interval instead of allowing
unlimited traffic. Bodies over the limit return 413, slow bodies 408. CORS preflight
is handled by CORS outside the limiter and never reaches business endpoints.

## Deployment (required before rollout)

1. Provision private Redis, with authentication/TLS where appropriate. Set
   `RATE_LIMIT__REDIS_URL` in the service environment or `.env`. Do not expose its
   port publicly. Use a dedicated instance with a memory ceiling and `noeviction`
   so memory pressure rejects requests instead of silently forgetting quotas.
2. Use a separate `RATE_LIMIT__PREFIX` for main and integration. Leave
   `RATE_LIMIT__ENABLED=true`; disabling it also disables body guards. Run
   `uv sync --frozen` and check Redis reachability before restarting the backend.
3. Restrict port 8000 to the reverse proxy/private network. Gunicorn trusts no
   forwarding headers by default. Set `FORWARDED_ALLOW_IPS` to only the real proxy
   peer addresses in the process environment (Gunicorn does not read `.env`).
   Never use `*`. The proxy must overwrite incoming `X-Forwarded-For`, not accept
   arbitrary client-supplied IPs. Without a trusted proxy all users share its quota.
4. Adapt `deploy/nginx-rate-limits.conf.example` to the actual proxy/TLS setup and
   validate with `nginx -t`. Behind a CDN, separately configure real-IP handling
   with that CDN's verified source ranges, and firewall the origin against bypass.
5. Check login/signup, HTTP 429 and `Retry-After`, and monitor 429/503 rates, Redis
   memory/latency and mail volume. Configure alerts in the deployment platform.

The local launcher provisions Redis on loopback port 56379 and disables proxy
header trust. Tests use database 15 with random prefixes and real Redis concurrency.
No production proxy, firewall or CDN settings were changed by this implementation.

This limits application abuse; it cannot protect a saturated network connection.
Volumetric DDoS mitigation requires the hosting provider/CDN. CAPTCHA and a durable
mail queue remain separate options, not features claimed by this patch.

Implementation reference: Redis documents atomic counters and rate-limiting races
at https://redis.io/docs/latest/commands/incr/ .

## Validation

77 backend tests pass against disposable PostgreSQL and real Redis, including
concurrent quota sharing, expiry, per-account limits across IPs, IPv6 grouping,
mail-route budgets, spoofed forwarding headers, oversized/slow bodies, storage
failure and signup blocked before further mail delivery. Local live HTTP checks
confirm 429 with `Retry-After` and successful organizer login/profile afterward.

## Simulated email verification in local development

`install/local.py` alone registers GET/POST `/v1/auth/local-verification`.
The public frontend probes this capability only on loopback hostnames, then offers
“Verificar compte de prova” on the pending-verification screen. The POST accepts
an email and runs the existing verification-token flow without sending mail.
It does not log the user in or grant organizer privileges. It requires a loopback
peer, loopback Host and (when present) loopback Origin. Normal `main:app` deployments
never register these routes; the `LOCAL` setting does not enable them.
