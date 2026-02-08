"""Hacker News Fetcher with 24-hour freshness filter."""

import time
from datetime import datetime, timezone
from typing import Any

from src.fetchers.base_fetcher import BaseFetcher
from src.models import NewsItem
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class HNFetcher(BaseFetcher):
    """Fetch top stories from Hacker News API."""

    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    def __init__(self):
        super().__init__(source_name="hn", source_type="tech", language="en")

    def _fetch_raw(self) -> list[dict]:
        """Fetch top story details from HN API."""
        resp = self._make_request(f"{self.BASE_URL}/topstories.json")
        story_ids = resp.json()

        stories = []
        checked = 0
        max_check = 50

        for story_id in story_ids:
            if checked >= max_check and len(stories) >= 3:
                break
            if len(stories) >= 20:
                break
            checked += 1

            story_resp = self._make_request(f"{self.BASE_URL}/item/{story_id}.json")
            story = story_resp.json()
            if not story:
                continue

            story_time = story.get("time", 0)
            score = story.get("score", 0)

            if not self._is_recent(story_time):
                continue
            if score < 50:
                continue

            stories.append(story)

        return stories

    def _parse_item(self, raw_item: Any) -> NewsItem:
        """Parse HN story dict into NewsItem."""
        story = raw_item
        url = story.get("url", "")
        if not url:
            url = f"https://news.ycombinator.com/item?id={story.get('id', '')}"

        ts = story.get("time", 0)
        timestamp = datetime.fromtimestamp(ts, tz=timezone.utc) if ts else datetime.now(tz=timezone.utc)

        return NewsItem(
            title=story.get("title", ""),
            url=url,
            source=self.source_name,
            timestamp=timestamp,
            content="",
            score=float(story.get("score", 0)),
            source_type=self.source_type,
            language=self.language,
            metadata={
                "by": story.get("by", ""),
                "hn_id": story.get("id"),
                "descendants": story.get("descendants", 0),
            },
        )

    @staticmethod
    def _is_recent(story_time: int, max_age_seconds: int = 86400) -> bool:
        """Check if a story is within the max age (default: 24 hours)."""
        return (int(time.time()) - story_time) <= max_age_seconds
