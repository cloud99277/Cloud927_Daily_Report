"""Jinri Toutiao (今日头条) Fetcher via RSSHub."""

from src.fetchers.china.base_china_fetcher import ChinaNewsFetcher


class JinriRemaiFetcher(ChinaNewsFetcher):
    """Fetch AI news from Jinri Toutiao via RSSHub."""

    def __init__(self):
        super().__init__(
            rsshub_url="https://rsshub.app/toutiao/rss/人工智能",
            source_name="jinri_remai",
        )
