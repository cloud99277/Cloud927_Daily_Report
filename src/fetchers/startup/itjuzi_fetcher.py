"""IT Juzi RSS fetcher."""

from src.fetchers.rss_fetcher import RSSFetcher


class ITJuziFetcher(RSSFetcher):
    """Fetch investment/funding news from IT Juzi."""

    def __init__(self):
        super().__init__(
            rss_url="https://rsshub.app/itjuzi/invest",
            source_name="itjuzi",
            source_type="startup",
            language="zh",
        )
