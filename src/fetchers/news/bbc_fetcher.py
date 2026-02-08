"""BBC World News Fetcher."""

from src.fetchers.rss_fetcher import RSSFetcher


class BBCWorldFetcher(RSSFetcher):
    """Fetch BBC World News."""

    def __init__(self):
        super().__init__(
            rss_url="http://feeds.bbci.co.uk/news/world/rss.xml",
            source_name="bbc_world",
            source_type="news",
            language="en",
        )
