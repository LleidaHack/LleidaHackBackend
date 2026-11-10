# Backend documentation

Start with the [repository README](../readme.md), [configuration](../README-config.md),
[local mail launcher](../install/LOCAL.md) and [test setup](../tests/README.md).

## Event operations

- [Operations API and Live configuration](EVENT_OPERATIONS.md)
- [Event readiness and organization tools](event-readiness.md)
- [Admission tickets, physical vouchers and check-in](checkin-tickets-vouchers.md)
- [Company judging portal](company-portal.md)
- [Challenge publication](CHALLENGE_PUBLICATION.md)
- [Devpost project import](DEVPOST_IMPORT.md) and [CSV example](examples/devpost-projects.csv)
- [Nickname and badge moderation](NICKNAME_AND_BADGE_MODERATION.md)
- [Participant uploads](participant-uploads.md)

## Integrations

- [Discord bot](DISCORD_BOT_INTEGRATION.md)
- [YouTube broadcast](YOUTUBE_LIVE.md)

## Deployment and maintenance

- [Production deployment and backup gates](production-deploy.md)
- [Health checks, restore and load rehearsal](infrastructure-readiness.md)
- [Request protection and Redis](request-protection.md)

Runbooks describe procedures and configuration, not proof that a particular host
currently has them installed. Verify the running release and environment before
operating production. Local seed scripts are not production migration tools.

## Historical reviews

These records explain previous releases and findings. They are not a current
inventory or the deployment entry point; use the runbooks above for routine work.

- [Production release of September 20, 2026](production-release-2026-09-20.md)
- [Backend security fixes](backend-security-fixes.md)
- [Public repository security review](public-repository-security.md)
