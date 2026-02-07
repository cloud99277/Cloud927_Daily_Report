"""GitHub Trending Fetcher using RSS and feedparser."""

import feedparser
from typing import Any
import textwrap
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


class GitHubFetcher:
    """Fetch GitHub trending repositories via RSS."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        # Using RSSHub for GitHub trending RSS feed
        self.base_url = "https://rsshub.app/github/trending/daily"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError))
    )
    def fetch_trending(self, language: str = "python", limit: int = 5) -> list[dict[str, Any]]:
        """
        Fetch top trending GitHub repositories for a given language.

        Args:
            language: Programming language to filter by (default: python)
            limit: Maximum number of repositories to return (default: 5)

        Returns:
            List of dictionaries containing repo name, description, stars, and url
        """
        url = f"{self.base_url}?lang={language}"
        feed = feedparser.parse(url, timeout=self.timeout)

        if feed.bozo:
            raise ConnectionError(f"Failed to parse RSS feed: {feed.bozo_exception}")

        if not hasattr(feed, 'entries'):
            raise ConnectionError("No entries found in RSS feed")

        repositories = []
        for entry in feed.entries[:limit]:
            repo_info = self._parse_entry(entry)
            repositories.append(repo_info)

        return repositories

    def _parse_entry(self, entry: feedparser.FeedParserDict) -> dict[str, Any]:
        """Parse a single RSS entry into structured repository data."""
        # Extract title (format: "repo_name by author")
        title = entry.get("title", "")
        parts = title.split(" by ")
        name = parts[0] if parts else title

        # Get description and truncate to < 300 chars
        description = entry.get("description", "")
        description = self._clean_html(description)
        description = textwrap.shorten(description, width=299, placeholder="...")

        # Extract stars from title or summary
        summary = entry.get("summary", "")
        stars = self._extract_stars(summary)

        # Get repository URL
        url = entry.get("link", "")

        return {
            "name": name,
            "description": description,
            "stars": stars,
            "url": url
        }

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)

    def _extract_stars(self, text: str) -> int:
        """Extract star count from text."""
        import re
        match = re.search(r'(\d+)\s*star', text, re.IGNORECASE)
        return int(match.group(1)) if match else 0

    def fetch_ai_trending(self, limit: int = 5) -> list[dict[str, Any]]:
        """Fetch AI-related trending repositories using topic filter."""
        # RSSHub doesn't support topic-based trending directly
        # We'll fetch Python trending and filter for AI-related repos
        repos = self.fetch_trending(language="python", limit=limit * 2)

        ai_keywords = ["ai", "machine-learning", "ml", "deep-learning", "neural",
                       "llm", "transformer", "gpt", "claude", "artificial"]

        ai_repos = []
        for repo in repos:
            repo_text = f"{repo['name']} {repo['description']}".lower()
            if any(keyword in repo_text for keyword in ai_keywords):
                ai_repos.append(repo)
                if len(ai_repos) >= limit:
                    break

        # If not enough AI repos found, return what we have
        return ai_repos


if __name__ == "__main__":
    import json

    fetcher = GitHubFetcher()
    repos = fetcher.fetch_trending(language="python", limit=5)
    print(json.dumps(repos, indent=2))
