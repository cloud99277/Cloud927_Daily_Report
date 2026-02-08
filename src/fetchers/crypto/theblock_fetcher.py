"""The Block RSS fetcher."""

from src.fetchers.rss_fetcher import RSSFetcher


class TheBlockFetcher(RSSFetcher):
    """Fetch crypto/blockchain news from The Block."""

    def __init__(self):
        super().__init__(
            rss_url="https://www.theblock.co/rss.xml",
            source_name="theblock",
            source_type="crypto",
        )
