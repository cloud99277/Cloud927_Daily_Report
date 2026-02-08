"""Pengpai (澎湃新闻) Fetcher via RSSHub."""

from src.fetchers.china.base_china_fetcher import ChinaNewsFetcher


class PengpaiFetcher(ChinaNewsFetcher):
    """Fetch news from The Paper (澎湃新闻) via RSSHub."""

    def __init__(self):
        super().__init__(
            rsshub_url="https://rsshub.app/thepaper",
            source_name="pengpai",
        )
