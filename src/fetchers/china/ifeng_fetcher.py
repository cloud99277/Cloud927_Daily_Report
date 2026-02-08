"""Ifeng (凤凰网) Fetcher via RSSHub."""

from src.fetchers.china.base_china_fetcher import ChinaNewsFetcher


class IfengFetcher(ChinaNewsFetcher):
    """Fetch news from Ifeng via RSSHub."""

    def __init__(self):
        super().__init__(
            rsshub_url="https://rsshub.app/ifeng/news",
            source_name="ifeng",
        )
