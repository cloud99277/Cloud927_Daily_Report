"""Reuters World News Fetcher."""

from src.fetchers.rss_fetcher import RSSFetcher


class ReutersFetcher(RSSFetcher):
    """Fetch Reuters world news."""

    def __init__(self):
        super().__init__(
            rss_url="https://www.reutersagency.com/feed/?best-topics=world-news&LOC=19254",
            source_name="reuters",
            source_type="news",
            language="en",
        )
