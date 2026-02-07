"""Reddit AI Fetcher - Curated AI discussions from Reddit."""
import json
import logging
from datetime import datetime
from typing import Any

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# Mock data as fallback
MOCK_REDDIT_POSTS = [
    {
        "title": "LocalLLaMA: Best setup for running Llama 3 70B on consumer hardware",
        "url": "https://.reddit.com/r/LocalLLaMA/comments/xxx/xxx",
        "source": "r/LocalLLaMA",
        "score": 1250,
        "comments": 89,
        "published_at": "2026-02-08T10:00:00",
    },
    {
        "title": "Claude vs GPT-4: Long-form writing comparison",
        "url": "https://www.reddit.com/r/Artificial/comments/xxx/xxx",
        "source": "r/Artificial",
        "score": 892,
        "comments": 156,
        "published_at": "2026-02-07T18:00:00",
    },
    {
        "title": "CrewAI vs AutoGen: Building multi-agent systems",
        "url": "https://www.reddit.com/r/LocalLLaMA/comments/yyy/yyy",
        "source": "r/LocalLLaMA",
        "score": 567,
        "comments": 45,
        "published_at": "2026-02-07T14:00:00",
    },
]


class RedditAIFetcher:
    """Fetch top AI discussions from Reddit."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.subreddits = [
            "r/LocalLLaMA",
            "r/Artificial",
            "r/MachineLearning",
            "r/Claude",
        ]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_subreddit(self, subreddit: str, limit: int = 5) -> list[dict]:
        """Fetch top posts from a subreddit."""
        try:
            url = f"https://www.reddit.com/{subreddit}/top.json?limit={limit}&t=day"
            headers = {
                "User-Agent": "Cloud927-Daily-Report/2.0",
            }
            response = requests.get(url, timeout=self.timeout, headers=headers)
            response.raise_for_status()
            data = response.json()

            posts = []
            for item in data.get("data", {}).get("children", [])[:limit]:
                post = item.get("data", {})
                posts.append({
                    "title": post.get("title", ""),
                    "url": f"https://reddit.com{post.get('permalink', '')}",
                    "source": subreddit,
                    "score": post.get("score", 0),
                    "comments": post.get("num_comments", 0),
                    "published_at": datetime.fromtimestamp(
                        post.get("created_utc", 0)
                    ).isoformat(),
                })

            return posts

        except Exception as e:
            logger.debug(f"Failed to fetch {subreddit}: {e}")
            return []

    def fetch(self) -> list[dict[str, Any]]:
        """Fetch top AI posts from all subreddits."""
        logger.info("Starting Reddit AI fetch")

        all_posts = []
        for subreddit in self.subreddits:
            posts = self._fetch_subreddit(subreddit, limit=5)
            all_posts.extend(posts)
            logger.info(f"Fetched {len(posts)} posts from {subreddit}")

        if not all_posts:
            logger.warning("No Reddit posts found, using mock data")
            return MOCK_REDDIT_POSTS

        # Sort by score and deduplicate by title
        all_posts.sort(key=lambda x: x.get("score", 0), reverse=True)
        seen_titles = set()
        unique_posts = []
        for post in all_posts:
            title_lower = post.get("title", "").lower()
            if title_lower not in seen_titles:
                seen_titles.add(title_lower)
                unique_posts.append(post)

        return unique_posts[:10]

    def to_json(self) -> str:
        """Return posts as JSON string."""
        return json.dumps(self.fetch(), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    fetcher = RedditAIFetcher()
    print(fetcher.to_json())
