"""Public alert updates over Redis pub/sub across API workers."""

import asyncio
import json
import logging
import time

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
    alerts, next_start = ops.live_alert_window(event_id)
    return {
        "type": "alerts",
        "alerts": alerts,
        "_next_start": next_start.timestamp() if next_start else None,
    }


def broadcast_alerts(event_id):
    # A transient Redis outage must not roll back an already committed alert.
    try:
        with Redis.from_url(settings.rate_limit.redis_url, socket_timeout=1) as redis:
            redis.publish(channel(event_id), json.dumps(public_alerts(event_id)))
    except RedisError:
        logger.warning("Alert broadcast unavailable; HTTP fallback remains active")


def broadcast_bull_reveal(event_id):
    with Redis.from_url(settings.rate_limit.redis_url, socket_timeout=1) as redis:
        return redis.publish(channel(event_id), json.dumps({"type": "bull_reveal"}))


def initial_alerts(event_id):
    with db():
        return public_alerts(event_id)


MAX_SOCKETS_PER_PROCESS = 2000
_open_sockets = 0
_redis_by_loop = {}


def shared_redis():
    # One connection pool per event loop (i.e. per worker process) instead of one
    # client per socket. Async clients are bound to the loop that created them.
    loop = asyncio.get_running_loop()
    client = _redis_by_loop.get(loop)
    if client is None:
        for stale in [k for k in _redis_by_loop if k.is_closed()]:
            _redis_by_loop.pop(stale, None)
        client = AsyncRedis.from_url(
            settings.rate_limit.redis_url, decode_responses=True
        )
        _redis_by_loop[loop] = client
    return client


def event_exists(event_id):
    from src.impl.Event.model import Event

    with db():
        return db.session.query(Event.id).filter_by(id=event_id).first() is not None


async def alert_socket(websocket: WebSocket, event_id: int):
    global _open_sockets
    if not await run_in_threadpool(event_exists, event_id):
        await websocket.close(code=1008)
        return
    if _open_sockets >= MAX_SOCKETS_PER_PROCESS:
        # 1013 = try again later; clients fall back to HTTP polling.
        await websocket.close(code=1013)
        return
    await websocket.accept()
    _open_sockets += 1
    redis = shared_redis()
    try:
        async with redis.pubsub() as subscription:
            await subscription.subscribe(channel(event_id))
            update = await run_in_threadpool(initial_alerts, event_id)
            next_start = update.pop("_next_start", None)
            await websocket.send_json(update)
            while True:
                timeout = (
                    15
                    if next_start is None
                    else min(15, max(0, next_start - time.time()))
                )
                message = await subscription.get_message(
                    ignore_subscribe_messages=True, timeout=timeout
                )
                if message and message["type"] == "message":
                    update = json.loads(message["data"])
                elif next_start is not None and next_start <= time.time():
                    update = await run_in_threadpool(initial_alerts, event_id)
                else:
                    await websocket.send_json({"type": "heartbeat"})
                    continue
                if update["type"] == "alerts":
                    next_start = update.pop("_next_start", None)
                await websocket.send_json(update)
    except (WebSocketDisconnect, RedisError, RuntimeError):
        pass
    finally:
        _open_sockets -= 1
