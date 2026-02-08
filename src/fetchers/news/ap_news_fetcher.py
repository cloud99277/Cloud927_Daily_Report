"""AP News Fetcher."""

import logging

from bs4 import BeautifulSoup

from src.fetchers.news.base_rss_fetcher import BaseRSSFetcher

logger = logging.getLogger(__name__)


class APNewsFetcher(BaseRSSFetcher):
    """Fetch AP News stories."""

    def __init__(self):
        super().__init__(
            rss_url="https://feeds.ap.org/feed/rss/AllStories",
            source_name="AP News",
            timeout=30,
            retry_attempts=3
        )

    def _parse_item(self, item: BeautifulSoup, item_data: dict) -> dict:
        item_data["source_type"] = "news"
        item_data["language"] = "en"

        categories = []
        for category in item.find_all("category"):
            cat_text = category.get_text()
            if cat_text and cat_text not in categories:
                categories.append(cat_text)
        item_data["categories"] = categories

        priority_categories = ["World News", "Politics", "Breaking"]
        item_data["priority"] = "high" if any(
            cat in item_data.get("categories", []) for cat in priority_categories
        ) else "normal"

        return item_data

    def fetch(self, limit: int = 15) -> list[dict]:
        return super().fetch(limit=limit)


if __name__ == "__main__":
    fetcher = APNewsFetcher()
    items = fetcher.fetch(limit=5)
    print(f"Fetched {len(items)} items from AP News")
