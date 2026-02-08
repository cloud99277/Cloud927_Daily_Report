"""Yahoo Finance RSS fetcher."""

from src.fetchers.rss_fetcher import RSSFetcher


class YahooFinanceFetcher(RSSFetcher):
    """Fetch financial news from Yahoo Finance."""

    def __init__(self):
        super().__init__(
            rss_url="https://finance.yahoo.com/news/rssindex",
            source_name="yahoo_finance",
            source_type="finance",
        )
