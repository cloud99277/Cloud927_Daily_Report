"""Hacker News Show HN Fetcher for new launches and projects."""

import logging
import time
from typing import Any

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# Mock data as fallback
MOCK_SHOW_HN_POSTS = [
    {
        "title": "Show HN: My new AI-powered code editor",
        "url": "https://github.com/user/code-editor",
        "score": 156,
        "author": "developer1",
        "time": int(time.time()) - 3600,
        "description": "A lightweight code editor with integrated AI completion and refactoring capabilities.",
        "comments": 42,
    },
    {
        "title": "Show HN: Open-source alternative to Notion",
        "url": "https://github.com/user/notes-app",
        "score": 89,
        "author": " indie_hacker",
        "time": int(time.time()) - 7200,
        "description": "A self-hosted note-taking app with similar features to Notion but 100% open source.",
        "comments": 23,
    },
    {
        "title": "Show HN: I built a CLI tool for API testing",
        "url": "https://github.com/user/http-cli",
        "score": 67,
        "author": "backend_dev",
        "time": int(time.time()) - 10800,
        "description": "A fast and intuitive command-line tool for testing REST APIs.",
        "comments": 15,
    },
]


class HNShowFetcher:
    """Fetch Show HN posts from Hacker News."""

    BASE_URL = "https://news.ycombinator.com"

    def __init__(self):
        self.logger = logger
        self.logger.info("HNShowFetcher initialized")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_html(self) -> str:
        """Fetch HTML page with retry logic."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(self.BASE_URL, timeout=30, headers=headers)
        response.raise_for_status()
        return response.text

    def _is_recent(self, story_time: int, max_age_seconds: int = 86400) -> bool:
        """Check if a story is within the max age (default: 24 hours)."""
        current_time = int(time.time())
        return (current_time - story_time) <= max_age_seconds

    def _format_time_ago(self, timestamp: int) -> str:
        """Format Unix timestamp to human-readable time ago."""
        seconds = int(time.time()) - timestamp
        if seconds < 3600:
            return f"{seconds // 60} minutes ago"
        elif seconds < 86400:
            return f"{seconds // 3600} hours ago"
        else:
            return f"{seconds // 86400} days ago"

    def _parse_story_row(self, row: Any, next_row: Any = None) -> dict[str, Any] | None:
        """Parse a single story row from HN page."""
        try:
            # Find the main title link
            title_link = row.select_one("a.storylink") or row.select_one("a[href]")
            if not title_link:
                return None

            title = title_link.get_text(strip=True)
            url = title_link.get("href", "")

            # Handle relative URLs
            if url.startswith("item?"):
                url = f"{self.BASE_URL}/{url}"

            # Get subtext row (contains score, author, time)
            subtext = row.select_one("subtext") or row.find_next_sibling("tr").select_one("subtext") if next_row else None
            if not subtext:
                # Try alternative structure
                subtext = row.select_one(".subtext") or (next_row.select_one(".subtext") if next_row else None)

            score_text = ""
            author = "Unknown"
            timestamp = int(time.time())

            if subtext:
                # Get score
                score_elem = subtext.select_one("span.score")
                if score_elem:
                    score_text = score_elem.get_text(strip=True)

                # Get author
                author_elem = subtext.select_one("a[href*='user']")
                if author_elem:
                    author = author_elem.get_text(strip=True)

                # Get time
                age_elem = subtext.select_one("span.age")
                if age_elem:
                    age_text = age_elem.get_text(strip=True)
                    timestamp = self._parse_age(age_text)

            # Parse score
            score = 0
            if score_text:
                import re
                match = re.search(r"(\d+)", score_text)
                if match:
                    score = int(match.group(1))

            # Get description from the title link's title attribute or sibling
            description = ""
            desc_link = row.select_one("a[href*='http']")
            if desc_link and desc_link.get("title"):
                description = desc_link.get("title")

            return {
                "title": title,
                "url": url or f"{self.BASE_URL}/item?id={int(time.time())}",
                "score": score,
                "author": author,
                "time": timestamp,
                "time_ago": self._format_time_ago(timestamp),
                "description": description,
            }
        except Exception as e:
            self.logger.debug(f"Failed to parse story row: {e}")
            return None

    def _parse_age(self, age_text: str) -> int:
        """Parse age string like '2 hours ago' to Unix timestamp."""
        import re
        current = int(time.time())

        patterns = [
            (r"(\d+)\s*minute", 60),
            (r"(\d+)\s*hour", 3600),
            (r"(\d+)\s*day", 86400),
            (r"(\d+)\s*week", 604800),
        ]

        for pattern, multiplier in patterns:
            match = re.search(pattern, age_text, re.IGNORECASE)
            if match:
                value = int(match.group(1))
                return current - (value * multiplier)

        return current

    def fetch_show_hn(self, limit: int = 5) -> list[dict[str, Any]]:
        """Fetch Show HN posts from HN Show page."""
        self.logger.info("Fetching Show HN posts")

        try:
            html = self._fetch_html()
            soup = BeautifulSoup(html, "html.parser")

            # Find all story rows - Show HN posts start with "Show HN:"
            stories = []
            rows = soup.select("tr.athing")

            for row in rows:
                title_elem = row.select_one("a.storylink") or row.select_one("a[href]")
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                if not title.startswith("Show HN:"):
                    continue

                # Get the subtext row
                subtext_row = row.find_next_sibling("tr")
                if subtext_row:
                    subtext = subtext_row.select_one(".subtext")
                    if subtext:
                        # Parse score
                        score_elem = subtext.select_one("span.score")
                        score = 0
                        if score_elem:
                            import re
                            match = re.search(r"(\d+)", score_elem.get_text())
                            if match:
                                score = int(match.group(1))

                        # Parse author
                        author_elem = subtext.select_one("a[href*='user']")
                        author = author_elem.get_text(strip=True) if author_elem else "Unknown"

                        # Parse time
                        age_elem = subtext.select_one("span.age")
                        timestamp = int(time.time())
                        time_ago = "just now"
                        if age_elem:
                            age_text = age_elem.get_text(strip=True)
                            timestamp = self._parse_age(age_text)
                            time_ago = age_text

                        # Parse URL
                        url = title_elem.get("href", "")
                        if url.startswith("item?"):
                            url = f"{self.BASE_URL}/{url}"

                        stories.append({
                            "title": title,
                            "url": url or f"{self.BASE_URL}/item?id={int(time.time())}",
                            "score": score,
                            "author": author,
                            "time": timestamp,
                            "time_ago": time_ago,
                            "description": title_elem.get("title", ""),
                        })

                if len(stories) >= limit:
                    break

            if stories:
                # Filter for recent posts (24h) and sort by score
                recent_stories = [s for s in stories if self._is_recent(s["time"])]
                if recent_stories:
                    stories = sorted(recent_stories, key=lambda x: x["score"], reverse=True)

                self.logger.info(f"Fetched {len(stories)} Show HN posts")
                return stories[:limit]
            else:
                self.logger.warning("No Show HN posts found, using mock data")
                return MOCK_SHOW_HN_POSTS[:limit]

        except Exception as e:
            self.logger.error(f"Failed to fetch Show HN: {e}, using mock data")
            return MOCK_SHOW_HN_POSTS[:limit]

    def fetch(self) -> dict[str, Any]:
        """Fetch Show HN posts, return structured JSON."""
        self.logger.info("Starting HN Show HN fetch")
        posts = self.fetch_show_hn(limit=5)

        # Filter recent posts
        recent_posts = [p for p in posts if self._is_recent(p["time"])]

        result = {
            "posts": posts,
            "recent_count": len(recent_posts),
            "total_count": len(posts),
        }
        self.logger.info(f"Fetched {len(posts)} posts, {len(recent_posts)} recent")
        return result

    def to_json(self) -> str:
        """Return posts as JSON string."""
        import json
        return json.dumps(self.fetch(), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import json

    fetcher = HNShowFetcher()
    result = fetcher.fetch()
    print(json.dumps(result, indent=2, ensure_ascii=False))
