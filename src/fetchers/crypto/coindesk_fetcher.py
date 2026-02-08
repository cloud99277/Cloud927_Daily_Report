"""CoinDesk RSS fetcher."""

from src.fetchers.rss_fetcher import RSSFetcher


class CoinDeskFetcher(RSSFetcher):
    """Fetch crypto/Web3 news from CoinDesk."""

    def __init__(self):
        super().__init__(
            rss_url="https://www.coindesk.com/arc/outboundfeeds/rss/",
            source_name="coindesk",
            source_type="crypto",
        )
