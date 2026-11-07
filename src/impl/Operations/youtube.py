"""Detect public YouTube broadcasts with a shared, quota-aware Redis cache."""

import json
import logging
import os

import httpx
from redis import Redis
from redis.exceptions import RedisError

from src.configuration.Settings import settings

logger = logging.getLogger(__name__)


def youtube_request(resource, key, **params):
    response = httpx.get(
        f"https://www.googleapis.com/youtube/v3/{resource}",
        params={"key": key, **params},
        timeout=8,
    )
    response.raise_for_status()
    return response.json().get("items", [])


def find_broadcast(key, channel_id):
    candidates = youtube_request(
        "search",
        key,
        part="snippet",
        channelId=channel_id,
        eventType="live",
        type="video",
        videoEmbeddable="true",
        maxResults=5,
    )
    ids = ",".join(item["id"]["videoId"] for item in candidates)
    return verify_broadcast(key, ids, channel_id) if ids else None


def verify_broadcast(key, video_ids, channel_id):
    videos = youtube_request(
        "videos",
        key,
        part="snippet,status,liveStreamingDetails",
        id=video_ids,
    )
    for video in videos:
        details = video.get("liveStreamingDetails", {})
        if (
            video.get("snippet", {}).get("channelId") == channel_id
            and details.get("actualStartTime")
            and not details.get("actualEndTime")
            and video.get("status", {}).get("embeddable")
            and video.get("status", {}).get("privacyStatus") == "public"
        ):
            return {"video_id": video["id"], "title": video["snippet"]["title"]}
    return None


def current_broadcast():
    key = os.getenv("YOUTUBE_API_KEY")
    if not key:
        return {"live": None}
    handle = os.getenv("YOUTUBE_CHANNEL_HANDLE", "LleidaHack").lstrip("@")
    prefix = f"{settings.rate_limit.prefix}:youtube:{handle}"
    try:
        with Redis.from_url(
            settings.rate_limit.redis_url, decode_responses=True, socket_timeout=1
        ) as cache:
            cached = cache.get(f"{prefix}:status")
            if cached:
                return json.loads(cached)
            # Fail closed when another worker is refreshing or Redis is unavailable.
            if not cache.set(f"{prefix}:lock", "1", nx=True, ex=60):
                return json.loads(cache.get(f"{prefix}:last") or '{"live": null}')
            try:
                channel_id = cache.get(f"{prefix}:channel")
                if not channel_id:
                    channels = youtube_request(
                        "channels", key, part="id", forHandle=handle
                    )
                    if not channels:
                        raise ValueError("YouTube channel not found")
                    channel_id = channels[0]["id"]
                    cache.setex(f"{prefix}:channel", 86400, channel_id)
                previous = cache.get(f"{prefix}:video")
                live = verify_broadcast(key, previous, channel_id) if previous else None
                if not live and not cache.get(f"{prefix}:searched"):
                    # Default supports the standard 100 searches/day allowance.
                    interval = max(
                        60, int(os.getenv("YOUTUBE_DISCOVERY_SECONDS", "900"))
                    )
                    cache.setex(f"{prefix}:searched", interval, "1")
                    live = find_broadcast(key, channel_id)
                if live:
                    cache.setex(f"{prefix}:video", 86400, live["video_id"])
                else:
                    cache.delete(f"{prefix}:video")
                result = {"live": live}
                cache.setex(f"{prefix}:status", 30, json.dumps(result))
                cache.setex(f"{prefix}:last", 60, json.dumps(result))
                return result
            except (httpx.HTTPError, ValueError, KeyError, TypeError):
                # Never log provider URLs: they contain the API key.
                logger.warning("YouTube broadcast discovery unavailable")
                cache.setex(f"{prefix}:status", 60, json.dumps({"live": None}))
                return {"live": None}
            finally:
                cache.delete(f"{prefix}:lock")
    except RedisError:
        return {"live": None}
