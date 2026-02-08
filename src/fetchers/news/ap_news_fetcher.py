"""AP News Fetcher."""

from src.fetchers.rss_fetcher import RSSFetcher


class APNewsFetcher(RSSFetcher):
    """Fetch AP News stories."""

    def __init__(self):
        super().__init__(
            rss_url="https://feeds.ap.org/feed/rss/AllStories",
            source_name="ap_news",
            source_type="news",
            language="en",
        )
