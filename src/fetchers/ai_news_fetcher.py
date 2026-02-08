"""AI News Fetcher for official AI company blogs."""

from datetime import datetime, timezone
from typing import Any

from bs4 import BeautifulSoup

from src.fetchers.base_fetcher import BaseFetcher
from src.models import NewsItem
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class AINewsFetcher(BaseFetcher):
    """Fetch AI news from official company blogs via HTML scraping."""

    SOURCES = [
        {
            "name": "OpenAI",
            "url": "https://openai.com/blog/",
            "selector": "article a[href*='/blog/']",
        },
        {
            "name": "Anthropic",
            "url": "https://www.anthropic.com/news",
            "selector": "article a[href*='/news/']",
        },
        {
            "name": "Google DeepMind",
            "url": "https://deepmind.google/blog",
            "selector": "article a[href*='/blog']",
        },
        {
            "name": "Meta AI",
            "url": "https://ai.meta.com/blog/",
            "selector": "article a[href*='/blog/']",
        },
    ]

    def __init__(self):
        super().__init__(source_name="ai_news", source_type="news", language="en")

    def _fetch_raw(self) -> list[dict]:
        """Scrape news items from all AI company blogs."""
        all_items: list[dict] = []
        for source in self.SOURCES:
            items = self._fetch_source(source)
            all_items.extend(items)
        return all_items

    def _fetch_source(self, source: dict) -> list[dict]:
        """Fetch news from a single blog source."""
        try:
            resp = self._make_request(source["url"])
            soup = BeautifulSoup(resp.text, "html.parser")
            items = []

            for elem in soup.select(source["selector"])[:5]:
                title_elem = (
                    elem.find(string=True, recursive=False)
                    or elem.find("h2")
                    or elem.find("h3")
                )
                title = (
                    title_elem.strip() if title_elem else elem.get_text(strip=True)
                )

                href = elem.get("href", "")
                if href and not href.startswith("http"):
                    base = source["url"].split("/blog")[0]
                    href = base + ("" if href.startswith("/") else "/") + href

                if title and len(title) > 10:
                    items.append({
                        "title": title,
                        "url": href if href.startswith("http") else source["url"],
                        "blog_source": source["name"],
                    })
            return items
        except Exception as e:
            logger.debug(f"Failed to fetch {source['name']}: {e}")
            return []

    def _parse_item(self, raw_item: Any) -> NewsItem:
        """Convert scraped blog item into NewsItem."""
        item = raw_item
        return NewsItem(
            title=item.get("title", ""),
            url=item.get("url", ""),
            source=self.source_name,
            timestamp=datetime.now(tz=timezone.utc),
            content="",
            source_type=self.source_type,
            language=self.language,
            metadata={"blog_source": item.get("blog_source", "")},
        )
