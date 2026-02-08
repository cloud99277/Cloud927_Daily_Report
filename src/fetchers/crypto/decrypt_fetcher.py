"""Decrypt RSS fetcher."""

from src.fetchers.rss_fetcher import RSSFetcher


class DecryptFetcher(RSSFetcher):
    """Fetch crypto/Web3 news from Decrypt."""

    def __init__(self):
        super().__init__(
            rss_url="https://decrypt.co/feed",
            source_name="decrypt",
            source_type="crypto",
        )
