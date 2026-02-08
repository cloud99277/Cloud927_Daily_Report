"""BBC World News Fetcher."""

import logging

from bs4 import BeautifulSoup

from src.fetchers.news.base_rss_fetcher import BaseRSSFetcher

logger = logging.getLogger(__name__)


class BBCWorldFetcher(BaseRSSFetcher):
    """Fetch BBC World News."""

    def __init__(self):
        super().__init__(
            rss_url="http://feeds.bbci.co.uk/news/world/rss.xml",
            source_name="BBC World",
            timeout=30,
            retry_attempts=3
        )

    def _parse_item(self, item: BeautifulSoup, item_data: dict) -> dict:
        item_data["source_type"] = "news"
        item_data["language"] = "en"

        priority_keywords = ["breaking", "urgent", "live updates", "developing"]
        title_lower = item_data.get("title", "").lower()
        item_data["priority"] = "high" if any(kw in title_lower for kw in priority_keywords) else "normal"

        return item_data

    def fetch(self, limit: int = 15) -> list[dict]:
        return super().fetch(limit=limit)


if __name__ == "__main__":
    fetcher = BBCWorldFetcher()
    items = fetcher.fetch(limit=5)
    print(f"Fetched {len(items)} items from BBC World")
