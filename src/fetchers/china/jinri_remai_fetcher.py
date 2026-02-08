"""Jinri Toutiao (今日头条) Fetcher via RSSHub."""

import logging

from src.fetchers.china.base_china_fetcher import ChinaNewsFetcher

logger = logging.getLogger(__name__)


class JinriRemaiFetcher(ChinaNewsFetcher):
    """Fetch AI news from Jinri Toutiao via RSSHub."""

    def __init__(self):
        super().__init__(
            rsshub_url="https://rsshub.app/toutiao/rss/人工智能",
            source_name="今日头条"
        )

    def fetch(self, limit: int = 15) -> list[dict]:
        """Fetch AI news from Jinri Toutiao."""
        return super().fetch(limit=limit)


if __name__ == "__main__":
    fetcher = JinriRemaiFetcher()
    items = fetcher.fetch(limit=5)
    print(f"Fetched {len(items)} items from 今日头条")
