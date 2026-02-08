"""Caixin (财新) Fetcher via RSSHub."""

from src.fetchers.china.base_china_fetcher import ChinaNewsFetcher


class CaixinFetcher(ChinaNewsFetcher):
    """Fetch news from Caixin (财新) via RSSHub."""

    def __init__(self):
        super().__init__(
            rsshub_url="https://rsshub.app/caixin",
            source_name="caixin",
        )
