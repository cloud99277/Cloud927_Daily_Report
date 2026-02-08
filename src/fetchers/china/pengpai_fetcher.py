"""Pengpai (澎湃新闻) Fetcher via RSSHub."""

import logging

from src.fetchers.china.base_china_fetcher import ChinaNewsFetcher

logger = logging.getLogger(__name__)


class PengpaiFetcher(ChinaNewsFetcher):
    """Fetch news from The Paper (澎湃新闻) via RSSHub."""

    def __init__(self):
        super().__init__(
            rsshub_url="https://rsshub.app/thepaper",
            source_name="澎湃新闻"
        )

    def fetch(self, limit: int = 15) -> list[dict]:
        """Fetch news from 澎湃新闻."""
        return super().fetch(limit=limit)


if __name__ == "__main__":
    fetcher = PengpaiFetcher()
    items = fetcher.fetch(limit=5)
    print(f"Fetched {len(items)} items from 澎湃新闻")
