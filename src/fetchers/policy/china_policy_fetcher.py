"""China government policy RSS fetcher."""

from src.fetchers.rss_fetcher import RSSFetcher


class ChinaPolicyFetcher(RSSFetcher):
    """Fetch policy news from China government sources."""

    def __init__(self):
        super().__init__(
            rss_url="https://rsshub.app/gov/zhengce/zuixin",
            source_name="china_policy",
            source_type="policy",
            language="zh",
        )
