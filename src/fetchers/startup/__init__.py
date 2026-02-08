"""Startup/investment fetchers."""

from src.fetchers.startup.techcrunch_fetcher import TechCrunchFetcher
from src.fetchers.startup.kr36_fetcher import Kr36Fetcher
from src.fetchers.startup.itjuzi_fetcher import ITJuziFetcher

__all__ = ["TechCrunchFetcher", "Kr36Fetcher", "ITJuziFetcher"]
