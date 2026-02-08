"""Sina (新浪) Fetcher via RSSHub."""

from src.fetchers.china.base_china_fetcher import ChinaNewsFetcher


class SinaFetcher(ChinaNewsFetcher):
    """Fetch news from Sina via RSSHub."""

    def __init__(self):
        super().__init__(
            rsshub_url="https://rsshub.app/sina/focus",
            source_name="sina",
        )
