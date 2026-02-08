"""Web3/Crypto fetchers."""

from src.fetchers.crypto.coindesk_fetcher import CoinDeskFetcher
from src.fetchers.crypto.theblock_fetcher import TheBlockFetcher
from src.fetchers.crypto.decrypt_fetcher import DecryptFetcher

__all__ = ["CoinDeskFetcher", "TheBlockFetcher", "DecryptFetcher"]
