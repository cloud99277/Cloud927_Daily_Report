"""Fetchers package."""

# Base classes
from src.fetchers.base_fetcher import BaseFetcher
from src.fetchers.rss_fetcher import RSSFetcher

# AI Tech Fetchers
from src.fetchers.hn_fetcher import HNFetcher
from src.fetchers.hn_show_fetcher import HNShowFetcher
from src.fetchers.github_fetcher import GitHubFetcher
from src.fetchers.hf_api_fetcher import HuggingFaceAPIFetcher
from src.fetchers.ai_news_fetcher import AINewsFetcher
from src.fetchers.ph_fetcher import ProductHuntFetcher
from src.fetchers.reddit_fetcher import RedditAIFetcher
from src.fetchers.v2ex_fetcher import V2EXFetcher

# News Fetchers
from src.fetchers.news.reuters_fetcher import ReutersFetcher
from src.fetchers.news.ap_news_fetcher import APNewsFetcher
from src.fetchers.news.bbc_fetcher import BBCWorldFetcher

# China Fetchers
from src.fetchers.china.jinri_remai_fetcher import JinriRemaiFetcher
from src.fetchers.china.sina_fetcher import SinaFetcher
from src.fetchers.china.ifeng_fetcher import IfengFetcher
from src.fetchers.china.pengpai_fetcher import PengpaiFetcher
from src.fetchers.china.caixin_fetcher import CaixinFetcher

# Supplementary Fetchers
from src.fetchers.twitter_fetcher import TwitterFetcher
from src.fetchers.arxiv_fetcher import ArxivFetcher

__all__ = [
    # Base
    "BaseFetcher",
    "RSSFetcher",
    # AI Tech
    "HNFetcher",
    "HNShowFetcher",
    "GitHubFetcher",
    "HuggingFaceAPIFetcher",
    "AINewsFetcher",
    "ProductHuntFetcher",
    "RedditAIFetcher",
    "V2EXFetcher",
    # News
    "ReutersFetcher",
    "APNewsFetcher",
    "BBCWorldFetcher",
    # China
    "JinriRemaiFetcher",
    "SinaFetcher",
    "IfengFetcher",
    "PengpaiFetcher",
    "CaixinFetcher",
    # Supplementary
    "TwitterFetcher",
    "ArxivFetcher",
]
