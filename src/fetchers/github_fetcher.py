"""GitHub Trending Fetcher using requests and BeautifulSoup."""

import requests
from bs4 import BeautifulSoup
from typing import Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


MOCK_DATA = [
    {
        "name": "microsoft/TypeScript",
        "description": "TypeScript is a superset of JavaScript that adds static typing.",
        "stars": 100000,
        "url": "https://github.com/microsoft/TypeScript",
        "language": "TypeScript"
    },
    {
        "name": "facebook/react",
        "description": "A library for building user interfaces.",
        "stars": 220000,
        "url": "https://github.com/facebook/react",
        "language": "JavaScript"
    },
    {
        "name": "vuejs/core",
        "description": "The Progressive JavaScript Framework.",
        "stars": 45000,
        "url": "https://github.com/vuejs/core",
        "language": "TypeScript"
    },
]


class GitHubFetcher:
    """Fetch GitHub trending repositories via HTML parsing."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.base_url = "https://github.com/trending"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.RequestException,))
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
        try:
            url = f"{self.base_url}/{language}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, timeout=self.timeout, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            articles = soup.select("article.Box-row")[:limit]

            repositories = []
            for article in articles:
                repo_info = self._parse_article(article, language)
                if repo_info:
                    repositories.append(repo_info)

            if repositories:
                return repositories
            else:
                raise ConnectionError("No repositories parsed from HTML")

        except Exception as e:
            print(f"GitHub fetch failed: {e}, using mock data")
            return MOCK_DATA[:limit]

    def _parse_article(self, article, language: str) -> dict[str, Any] | None:
        """Parse a single article element into structured repository data."""
        try:
            # Repo URL - find link matching pattern /owner/repo (not /login, not single name)
            repo_link = None
            for link in article.select("a"):
                href = link.get("href", "")
                # Skip login redirects and single-name links (contributors)
                if href and "/" in href and not href.startswith("/login"):
                    parts = href.strip("/").split("/")
                    if len(parts) == 2 and len(parts[0]) > 1:  # owner/repo format
                        repo_link = href
                        break

            if not repo_link:
                return None

            name = repo_link.strip("/")

            # Full URL
            url = f"https://github.com{repo_link}"

            # Description - get text after the h2 with repo name
            desc_elem = article.select_one("p")
            description = desc_elem.get_text(strip=True) if desc_elem else ""

            # Stars - find element with comma-formatted number followed by star
            article_text = article.get_text()
            import re
            star_match = re.search(r'([\d,]+)\s*star', article_text, re.IGNORECASE)
            stars = self._parse_stars(star_match.group(1)) if star_match else 0

            return {
                "name": name,
                "description": description[:200] if description else "No description",
                "stars": stars,
                "url": url,
                "language": language
            }
        except Exception as e:
            print(f"Parse error: {e}")
            return None

    def _parse_stars(self, text: str) -> int:
        """Convert star count text to integer (e.g., '1.2k' -> 1200)."""
        text = text.strip().lower().replace(",", "")
        multipliers = {"k": 1000, "m": 1000000}
        if text[-1] in multipliers:
            try:
                return int(float(text[:-1]) * multipliers[text[-1]])
            except ValueError:
                return 0
        try:
            return int(text)
        except ValueError:
            return 0

    def fetch_ai_trending(self, limit: int = 5) -> list[dict[str, Any]]:
        """Fetch AI-related trending repositories."""
        # Fetch Python trending and filter for AI-related
        repos = self.fetch_trending(language="python", limit=limit * 2)

        ai_keywords = ["ai", "machine-learning", "ml", "deep-learning", "neural",
                       "llm", "transformer", "gpt", "claude", "artificial", "pytorch",
                       "tensorflow", "huggingface", "langchain", "agent"]

        ai_repos = []
        for repo in repos:
            repo_text = f"{repo['name']} {repo['description']}".lower()
            if any(keyword in repo_text for keyword in ai_keywords):
                ai_repos.append(repo)
                if len(ai_repos) >= limit:
                    break

        return ai_repos if ai_repos else MOCK_DATA[:limit]


if __name__ == "__main__":
    import json

    fetcher = GitHubFetcher()
    repos = fetcher.fetch_trending(language="python", limit=5)
    print(json.dumps(repos, indent=2, ensure_ascii=False))
