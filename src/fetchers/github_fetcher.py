"""GitHub Trending Fetcher."""

import re
from datetime import datetime, timezone
from typing import Any

from bs4 import BeautifulSoup

from src.fetchers.base_fetcher import BaseFetcher
from src.models import NewsItem
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class GitHubFetcher(BaseFetcher):
    """Fetch GitHub trending repositories via HTML parsing."""

    def __init__(self):
        super().__init__(source_name="github", source_type="tech", language="en")
        self.base_url = "https://github.com/trending"

    def _fetch_raw(self) -> list[dict]:
        """Fetch trending repos for python and typescript."""
        repos = []
        for lang in ("python", "typescript"):
            resp = self._make_request(f"{self.base_url}/{lang}")
            soup = BeautifulSoup(resp.text, "html.parser")
            for article in soup.select("article.Box-row")[:10]:
                parsed = self._parse_article(article, lang)
                if parsed:
                    repos.append(parsed)
        return repos

    def _parse_item(self, raw_item: Any) -> NewsItem:
        """Convert parsed repo dict into NewsItem."""
        repo = raw_item
        return NewsItem(
            title=repo.get("name", ""),
            url=repo.get("url", ""),
            source=self.source_name,
            timestamp=datetime.now(tz=timezone.utc),
            content=repo.get("description", ""),
            score=float(repo.get("stars", 0)),
            source_type=self.source_type,
            language=self.language,
            metadata={"prog_language": repo.get("prog_language", "")},
        )

    def _parse_article(self, article: Any, language: str) -> dict | None:
        """Parse a single trending repo article element."""
        try:
            repo_link = None
            for link in article.select("a"):
                href = link.get("href", "")
                if href and "/" in href and not href.startswith("/login"):
                    parts = href.strip("/").split("/")
                    if len(parts) == 2 and len(parts[0]) > 1:
                        repo_link = href
                        break
            if not repo_link:
                return None

            name = repo_link.strip("/")
            url = f"https://github.com{repo_link}"

            desc_elem = article.select_one("p")
            description = desc_elem.get_text(strip=True) if desc_elem else ""

            article_text = article.get_text()
            star_match = re.search(r'([\d,]+)\s*star', article_text, re.IGNORECASE)
            stars = self._parse_stars(star_match.group(1)) if star_match else 0

            return {
                "name": name,
                "description": description[:200] if description else "",
                "stars": stars,
                "url": url,
                "prog_language": language,
            }
        except Exception as e:
            logger.warning(f"Parse error: {e}")
            return None

    @staticmethod
    def _parse_stars(text: str) -> int:
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
