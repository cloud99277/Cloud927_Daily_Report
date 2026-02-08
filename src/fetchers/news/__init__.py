"""News fetchers package."""

from src.fetchers.news.reuters_fetcher import ReutersFetcher
from src.fetchers.news.ap_news_fetcher import APNewsFetcher
from src.fetchers.news.bbc_fetcher import BBCWorldFetcher

__all__ = [
    "ReutersFetcher",
    "APNewsFetcher",
    "BBCWorldFetcher",
]
