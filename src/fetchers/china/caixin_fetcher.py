"""Caixin (财新) Fetcher via RSSHub."""

import logging

from src.fetchers.china.base_china_fetcher import ChinaNewsFetcher

logger = logging.getLogger(__name__)


class CaixinFetcher(ChinaNewsFetcher):
    """Fetch news from Caixin (财新) via RSSHub."""

    def __init__(self):
        super().__init__(
            rsshub_url="https://rsshub.app/caixin",
            source_name="财新"
        )

    def fetch(self, limit: int = 15) -> list[dict]:
        """Fetch news from 财新."""
        return super().fetch(limit=limit)


if __name__ == "__main__":
    fetcher = CaixinFetcher()
    items = fetcher.fetch(limit=5)
    print(f"Fetched {len(items)} items from 财新")
