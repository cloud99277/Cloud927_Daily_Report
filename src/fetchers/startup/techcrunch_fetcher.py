"""TechCrunch RSS fetcher."""

from src.fetchers.rss_fetcher import RSSFetcher


class TechCrunchFetcher(RSSFetcher):
    """Fetch startup/tech news from TechCrunch."""

    def __init__(self):
        super().__init__(
            rss_url="https://techcrunch.com/feed/",
            source_name="techcrunch",
            source_type="startup",
        )
