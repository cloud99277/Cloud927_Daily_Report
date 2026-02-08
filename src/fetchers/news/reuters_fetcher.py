"""Reuters World News Fetcher."""

import logging
from typing import Any

from bs4 import BeautifulSoup

from src.fetchers.news.base_rss_fetcher import BaseRSSFetcher

logger = logging.getLogger(__name__)


class ReutersFetcher(BaseRSSFetcher):
    """Fetch Reuters world news."""

    def __init__(self):
        """Initialize Reuters fetcher."""
        super().__init__(
            rss_url="https://www.reutersagency.com/feed/?best-topics=world-news&LOC=19254",
            source_name="Reuters",
            timeout=30,
            retry_attempts=3
        )

    def _parse_item(self, item: BeautifulSoup, item_data: dict) -> dict:
        """Parse Reuters-specific item fields."""
        item_data["source_type"] = "news"
        item_data["language"] = "en"

        if "categories" not in item_data or not item_data["categories"]:
            categories = []
            for category in item.find_all("category"):
                cat_text = category.get_text()
                if cat_text and cat_text not in categories:
                    categories.append(cat_text)
            item_data["categories"] = categories

        priority_categories = ["World News", "Politics", "Breaking News"]
        item_data["priority"] = "high" if any(
            cat in item_data.get("categories", []) for cat in priority_categories
        ) else "normal"

        return item_data

    def fetch(self, limit: int = 15) -> list[dict]:
        """Fetch Reuters world news."""
        return super().fetch(limit=limit)


if __name__ == "__main__":
    fetcher = ReutersFetcher()
    items = fetcher.fetch(limit=5)
    print(f"Fetched {len(items)} items from Reuters")
