"""Financial Times RSS fetcher."""

from src.fetchers.rss_fetcher import RSSFetcher


class FTFetcher(RSSFetcher):
    """Fetch financial/macro news from Financial Times."""

    def __init__(self):
        super().__init__(
            rss_url="https://www.ft.com/rss/home",
            source_name="ft",
            source_type="finance",
        )
