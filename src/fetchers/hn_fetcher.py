import logging
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class HNFetcher:
    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    def __init__(self):
        self.logger = logger
        self.logger.info("HNFetcher initialized")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.RequestException,))
    )
    def _fetch(self, url: str) -> dict | list | None:
        """Make HTTP request with retry logic."""
        self.logger.debug(f"Fetching: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()

    def get_top_stories(self, limit: int = 10) -> list[dict]:
        """Fetch top stories from HN."""
        top_stories_url = f"{self.BASE_URL}/topstories.json"
        story_ids = self._fetch(top_stories_url)

        stories = []
        for story_id in story_ids[:limit]:
            story_url = f"{self.BASE_URL}/item/{story_id}.json"
            story = self._fetch(story_url)
            if story and story.get("score", 0) > 150:
                stories.append({
                    "title": story.get("title"),
                    "url": story.get("url"),
                    "score": story.get("score"),
                    "by": story.get("by")
                })
                if len(stories) >= 5:
                    break
        return stories

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
            if comment and comment.get("text") and len(comment["text"]) < 200:
                comments.append({
                    "text": comment.get("text"),
                    "by": comment.get("by")
                })
                if len(comments) >= limit:
                    break
        return comments

    def fetch(self) -> dict:
        """Fetch top stories and comments, return structured JSON."""
        self.logger.info("Starting HN fetch")
        stories = self.get_top_stories(limit=5)
        comments = self.get_top_comments(limit=3)
        result = {
            "stories": stories,
            "comments": comments
        }
        self.logger.info(f"Fetched {len(stories)} stories, {len(comments)} comments")
        return result
