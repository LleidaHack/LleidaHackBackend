"""Manual broadcast configuration remains safe and backwards compatible."""

import unittest

from pydantic import ValidationError

from src.impl.Operations.schema import EventConfig


class ManualBroadcastTests(unittest.TestCase):
    def test_old_channel_links_remain_valid_when_disabled(self):
        config = EventConfig(stream_url="https://youtube.com/@LleidaHack")
        self.assertFalse(config.stream_enabled)

    def test_supported_video_links_round_trip(self):
        for url in [
            "https://youtu.be/abcdefghijk",
            "https://www.youtube.com/watch?v=abcdefghijk&t=5",
            "https://youtube.com/live/abcdefghijk?si=test",
        ]:
            with self.subTest(url=url):
                config = EventConfig(stream_url=url, stream_enabled=True)
                self.assertTrue(
                    EventConfig.model_validate(
                        config.model_dump(mode="json")
                    ).stream_enabled
                )

    def test_enabled_requires_a_youtube_video(self):
        for url in [
            None,
            "https://youtube.com/@LleidaHack",
            "https://youtube.com.evil.test/watch?v=abcdefghijk",
            "https://youtu.be/short",
        ]:
            with self.subTest(url=url), self.assertRaises(ValidationError):
                EventConfig(stream_url=url, stream_enabled=True)
