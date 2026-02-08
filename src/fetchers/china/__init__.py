"""China fetchers package."""

from src.fetchers.china.jinri_remai_fetcher import JinriRemaiFetcher
from src.fetchers.china.sina_fetcher import SinaFetcher
from src.fetchers.china.ifeng_fetcher import IfengFetcher
from src.fetchers.china.pengpai_fetcher import PengpaiFetcher
from src.fetchers.china.caixin_fetcher import CaixinFetcher

__all__ = [
    "JinriRemaiFetcher",
    "SinaFetcher",
    "IfengFetcher",
    "PengpaiFetcher",
    "CaixinFetcher",
]
