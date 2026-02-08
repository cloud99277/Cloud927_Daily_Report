"""Reddit AI Fetcher - Curated AI discussions from Reddit."""

from datetime import datetime, timezone
from typing import Any

from src.fetchers.base_fetcher import BaseFetcher
from src.models import NewsItem
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class RedditAIFetcher(BaseFetcher):
    """Fetch top AI discussions from Reddit."""

    SUBREDDITS = [
        "r/LocalLLaMA",
        "r/Artificial",
        "r/MachineLearning",
        "r/Claude",
    ]

    def __init__(self):
        super().__init__(source_name="reddit", source_type="social", language="en")

    def _fetch_raw(self) -> list[dict]:
        """Fetch top posts from all AI subreddits."""
        all_posts: list[dict] = []
        for subreddit in self.SUBREDDITS:
            posts = self._fetch_subreddit(subreddit)
            all_posts.extend(posts)

        # Sort by score, deduplicate by title
        all_posts.sort(key=lambda x: x.get("score", 0), reverse=True)
        seen: set[str] = set()
        unique: list[dict] = []
        for post in all_posts:
            key = post.get("title", "").lower()
            if key not in seen:
                seen.add(key)
                unique.append(post)
        return unique

    def _fetch_subreddit(self, subreddit: str, limit: int = 5) -> list[dict]:
        """Fetch top posts from a single subreddit."""
        try:
            url = f"https://www.reddit.com/{subreddit}/top.json?limit={limit}&t=day"
            resp = self._make_request(url)
            data = resp.json()
            posts = []
            for item in data.get("data", {}).get("children", [])[:limit]:
                post = item.get("data", {})
                posts.append({
                    "title": post.get("title", ""),
                    "permalink": post.get("permalink", ""),
                    "subreddit": subreddit,
                    "score": post.get("score", 0),
                    "num_comments": post.get("num_comments", 0),
                    "created_utc": post.get("created_utc", 0),
                })
            return posts
        except Exception as e:
            logger.debug(f"Failed to fetch {subreddit}: {e}")
            return []

    def _parse_item(self, raw_item: Any) -> NewsItem:
        """Convert Reddit post dict into NewsItem."""
        post = raw_item
        ts = post.get("created_utc", 0)
        timestamp = (
            datetime.fromtimestamp(ts, tz=timezone.utc)
            if ts
            else datetime.now(tz=timezone.utc)
        )
        permalink = post.get("permalink", "")
        url = f"https://reddit.com{permalink}" if permalink else ""

        return NewsItem(
            title=post.get("title", ""),
            url=url,
            source=self.source_name,
            timestamp=timestamp,
            content="",
            score=float(post.get("score", 0)),
            source_type=self.source_type,
            language=self.language,
            metadata={
                "subreddit": post.get("subreddit", ""),
                "num_comments": post.get("num_comments", 0),
            },
        )
