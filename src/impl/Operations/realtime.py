"""Public alert updates over Redis pub/sub across API workers."""

import json
import logging

from fastapi import WebSocket, WebSocketDisconnect
from fastapi_sqlalchemy import db
from redis import Redis
from redis.asyncio import Redis as AsyncRedis
from redis.exceptions import RedisError
from starlette.concurrency import run_in_threadpool

from src.configuration.Settings import settings
from src.impl.Operations import service as ops

logger = logging.getLogger(__name__)


def channel(event_id):
    return f"{settings.rate_limit.prefix}:operations:{event_id}:alerts"


def public_alerts(event_id):
    return {"type": "alerts", "alerts": ops.snapshot(event_id)["alerts"]}


def broadcast_alerts(event_id):
    # A transient Redis outage must not roll back an already committed alert.
    try:
        with Redis.from_url(settings.rate_limit.redis_url, socket_timeout=1) as redis:
            redis.publish(channel(event_id), json.dumps(public_alerts(event_id)))
    except RedisError:
        logger.warning("Alert broadcast unavailable; HTTP fallback remains active")


def initial_alerts(event_id):
    with db():
        return public_alerts(event_id)


async def alert_socket(websocket: WebSocket, event_id: int):
    await websocket.accept()
    redis = AsyncRedis.from_url(settings.rate_limit.redis_url, decode_responses=True)
    try:
        async with redis.pubsub() as subscription:
            await subscription.subscribe(channel(event_id))
            await websocket.send_json(await run_in_threadpool(initial_alerts, event_id))
            while True:
                message = await subscription.get_message(
                    ignore_subscribe_messages=True, timeout=15
                )
                if message and message["type"] == "message":
                    await websocket.send_text(message["data"])
                else:
                    await websocket.send_json({"type": "heartbeat"})
    except (WebSocketDisconnect, RedisError, RuntimeError):
        pass
    finally:
        await redis.aclose()
