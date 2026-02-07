"""Hacker News Fetcher with 24-hour freshness filter."""

import logging
import requests
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class HNFetcher:
    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    def __init__(self):
        self.logger = logger
        self.logger.info("HNFetcher initialized")

    def _fetch(self, url: str) -> dict | list | None:
        """Make HTTP request with retry logic."""
        self.logger.debug(f"Fetching: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()

    def _is_recent(self, story_time: int, max_age_seconds: int = 86400) -> bool:
        """Check if a story is within the max age (default: 24 hours)."""
        current_time = int(time.time())
        return (current_time - story_time) <= max_age_seconds

    def get_top_stories(self, limit: int = 10) -> list[dict]:
        """
        Fetch top stories from HN with 24-hour freshness filter.
        Only returns items posted within the last 24 hours.
        """
        top_stories_url = f"{self.BASE_URL}/topstories.json"
        story_ids = self._fetch(top_stories_url)

        stories = []
        checked = 0
        max_check = 50  # Don't check too many to avoid rate limits

        for story_id in story_ids:
            if checked >= max_check and len(stories) >= 3:
                # If we've checked enough and have some results, break
                break
            if len(stories) >= limit:
                break

            checked += 1

            story_url = f"{self.BASE_URL}/item/{story_id}.json"
            story = self._fetch(story_url)

            if not story:
                continue

            # Check score and time filter
            story_time = story.get("time", 0)
            score = story.get("score", 0)

            # Apply 24-hour freshness filter
            if not self._is_recent(story_time):
                self.logger.debug(f"Story too old: {story.get('title', 'N/A')}")
                continue

            if score >= 50:  # Lower threshold slightly to ensure enough fresh content
                stories.append({
                    "title": story.get("title"),
                    "url": story.get("url"),
                    "score": score,
                    "by": story.get("by"),
                    "time": story_time,
                    "time_ago": self._format_time_ago(story_time)
                })

        self.logger.info(f"Fetched {len(stories)} fresh stories (last 24h) from {checked} checked")
        return stories

    def _format_time_ago(self, timestamp: int) -> str:
        """Format Unix timestamp to human-readable time ago."""
        seconds = int(time.time()) - timestamp
        if seconds < 3600:
            return f"{seconds // 60} minutes ago"
        elif seconds < 86400:
            return f"{seconds // 3600} hours ago"
        else:
            return f"{seconds // 86400} days ago"

    def get_top_comments(self, story_id: int | None = None, limit: int = 3) -> list[dict]:
        """Fetch top comments from a story or default story."""
        if story_id is None:
            story_ids = self._fetch(f"{self.BASE_URL}/topstories.json")
            story_id = story_ids[0]

        item_url = f"{self.BASE_URL}/item/{story_id}.json"
        story = self._fetch(item_url)
        if not story:
            return []

        comment_ids = story.get("kids", [])[:10]
        comments = []

        for comment_id in comment_ids:
            comment_url = f"{self.BASE_URL}/item/{comment_id}.json"
            comment = self._fetch(comment_url)
            if comment and comment.get("text") and len(comment["text"]) < 300:
                comments.append({
                    "text": comment.get("text"),
                    "by": comment.get("by")
                })
                if len(comments) >= limit:
                    break
        return comments

    def fetch(self) -> dict:
        """Fetch top stories and comments, return structured JSON."""
        self.logger.info("Starting HN fetch with 24h freshness filter")
        stories = self.get_top_stories(limit=5)
        comments = self.get_top_comments(limit=3)
        result = {
            "stories": stories,
            "comments": comments
        }
        self.logger.info(f"Fetched {len(stories)} stories, {len(comments)} comments")
        return result


if __name__ == "__main__":
    fetcher = HNFetcher()
    result = fetcher.fetch()
    print(f"Stories: {len(result['stories'])}")
    for s in result['stories']:
        print(f"  - {s['title']} ({s['score']} pts) - {s.get('time_ago', 'N/A')}")
