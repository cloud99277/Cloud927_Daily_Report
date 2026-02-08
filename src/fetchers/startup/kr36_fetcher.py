"""36Kr RSS fetcher."""

from src.fetchers.rss_fetcher import RSSFetcher


class Kr36Fetcher(RSSFetcher):
    """Fetch startup/investment news from 36Kr."""

    def __init__(self):
        super().__init__(
            rss_url="https://rsshub.app/36kr/news",
            source_name="36kr",
            source_type="startup",
            language="zh",
        )
