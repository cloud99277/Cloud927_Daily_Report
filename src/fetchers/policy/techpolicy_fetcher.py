"""Tech policy RSS fetcher (The Verge Policy)."""

from src.fetchers.rss_fetcher import RSSFetcher


class TechPolicyFetcher(RSSFetcher):
    """Fetch tech policy news from The Verge."""

    def __init__(self):
        super().__init__(
            rss_url="https://www.theverge.com/rss/policy/index.xml",
            source_name="techpolicy",
            source_type="policy",
        )
