"""Sina (新浪) Fetcher via RSSHub."""

import logging

from src.fetchers.china.base_china_fetcher import ChinaNewsFetcher

logger = logging.getLogger(__name__)


class SinaFetcher(ChinaNewsFetcher):
    """Fetch news from Sina via RSSHub."""

    def __init__(self):
        super().__init__(
            rsshub_url="https://rsshub.app/sina/focus",
            source_name="新浪"
        )

    def fetch(self, limit: int = 15) -> list[dict]:
        """Fetch news from Sina."""
        return super().fetch(limit=limit)


if __name__ == "__main__":
    fetcher = SinaFetcher()
    items = fetcher.fetch(limit=5)
    print(f"Fetched {len(items)} items from 新浪")
