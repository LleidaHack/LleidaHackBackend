"""Broadcast eligibility checks without provider requests."""

import unittest
from unittest.mock import patch

from src.impl.Operations.youtube import current_broadcast, verify_broadcast


class BroadcastTests(unittest.TestCase):
    def video(self, **details):
        return {
            "id": "abcdefghijk",
            "snippet": {"channelId": "official", "title": "Live"},
            "status": {"embeddable": True, "privacyStatus": "public"},
            "liveStreamingDetails": details,
        }

    @patch("src.impl.Operations.youtube.youtube_request")
    def test_only_active_public_embeddable_channel_streams_are_returned(self, request):
        live = self.video(actualStartTime="2026-11-06T18:00:00Z")
        request.return_value = [live]
        self.assertEqual(
            verify_broadcast("secret", "abcdefghijk", "official")["video_id"],
            "abcdefghijk",
        )
        self.assertIsNone(verify_broadcast("secret", "abcdefghijk", "other"))
        for field, value in [("embeddable", False), ("privacyStatus", "private")]:
            request.return_value = [
                {**live, "status": {**live["status"], field: value}}
            ]
            self.assertIsNone(verify_broadcast("secret", "abcdefghijk", "official"))
        for details in [
            {},
            {"scheduledStartTime": "later"},
            {"actualStartTime": "earlier", "actualEndTime": "now"},
        ]:
            request.return_value = [self.video(**details)]
            self.assertIsNone(verify_broadcast("secret", "abcdefghijk", "official"))

    @patch.dict("os.environ", {"YOUTUBE_API_KEY": ""})
    @patch("src.impl.Operations.youtube.youtube_request")
    def test_unconfigured_provider_is_hidden_without_requests(self, request):
        self.assertEqual(current_broadcast(), {"live": None})
        request.assert_not_called()

    @patch.dict("os.environ", {"YOUTUBE_API_KEY": "test-key"})
    @patch("src.impl.Operations.youtube.Redis.from_url")
    @patch("src.impl.Operations.youtube.youtube_request")
    def test_shared_cache_avoids_provider_requests(self, request, redis):
        redis.return_value.__enter__.return_value.get.return_value = (
            '{"live": {"video_id": "abcdefghijk", "title": "Live"}}'
        )
        self.assertEqual(current_broadcast()["live"]["video_id"], "abcdefghijk")
        request.assert_not_called()

    @patch.dict("os.environ", {"YOUTUBE_API_KEY": "test-key"})
    @patch("src.impl.Operations.youtube.Redis.from_url")
    @patch("src.impl.Operations.youtube.youtube_request")
    def test_redis_failure_does_not_fan_out_to_provider(self, request, redis):
        from redis.exceptions import RedisError

        redis.side_effect = RedisError("Unavailable")
        self.assertEqual(current_broadcast(), {"live": None})
        request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
