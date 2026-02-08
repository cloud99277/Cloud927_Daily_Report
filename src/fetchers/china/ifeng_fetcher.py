"""Ifeng (凤凰网) Fetcher via RSSHub."""

import logging

from src.fetchers.china.base_china_fetcher import ChinaNewsFetcher

logger = logging.getLogger(__name__)


class IfengFetcher(ChinaNewsFetcher):
    """Fetch news from Ifeng via RSSHub."""

    def __init__(self):
        super().__init__(
            rsshub_url="https://rsshub.app/ifeng/news",
            source_name="凤凰网"
        )

    def fetch(self, limit: int = 15) -> list[dict]:
        """Fetch news from Ifeng."""
        return super().fetch(limit=limit)


if __name__ == "__main__":
    fetcher = IfengFetcher()
    items = fetcher.fetch(limit=5)
    print(f"Fetched {len(items)} items from 凤凰网")
