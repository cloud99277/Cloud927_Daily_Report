"""Bloomberg RSS fetcher."""

from src.fetchers.rss_fetcher import RSSFetcher


class BloombergFetcher(RSSFetcher):
    """Fetch financial/market news from Bloomberg."""

    def __init__(self):
        super().__init__(
            rss_url="https://feeds.bloomberg.com/markets/news.rss",
            source_name="bloomberg",
            source_type="finance",
        )
