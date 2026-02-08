"""Universal base class for all Cloud927 fetchers."""

import random
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.config import Config
from src.models import NewsItem
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]


class BaseFetcher(ABC):
    """Universal base class for all fetchers."""

    def __init__(self, source_name: str, source_type: str = "", language: str = "en"):
        self.source_name = source_name
        self.source_type = source_type
        self.language = language

        cfg = Config()
        source_cfg = cfg.get_source_config(source_name) or {}
        self.enabled = source_cfg.get("enabled", True)
        self.timeout = source_cfg.get("timeout_seconds", 30)
        self.retry_attempts = source_cfg.get("retry_attempts", 3)

    @abstractmethod
    def _fetch_raw(self) -> Any:
        """Fetch raw data from source. Subclasses implement this."""

    @abstractmethod
    def _parse_item(self, raw_item: Any) -> NewsItem:
        """Parse a raw item into NewsItem. Subclasses implement this."""

    def fetch(self, limit: int = 20) -> list[NewsItem]:
        """Main fetch method with retry, error handling, config check."""
        if not self.enabled:
            logger.info(f"Source '{self.source_name}' is disabled, skipping")
            return []

        logger.info(f"Fetching from {self.source_name}")
        try:
            raw = self._fetch_with_retry()
            if raw is None:
                return []

            if not isinstance(raw, list):
                raw = [raw]

            items: list[NewsItem] = []
            for entry in raw[:limit]:
                try:
                    item = self._parse_item(entry)
                    items.append(item)
                except Exception as e:
                    logger.warning(f"Failed to parse item from {self.source_name}: {e}")
                    continue

            logger.info(f"Fetched {len(items)} items from {self.source_name}")
            return items
        except Exception as e:
            logger.error(f"Failed to fetch {self.source_name}: {e}")
            return []

    def _fetch_with_retry(self) -> Any:
        """Wrap _fetch_raw with tenacity retry based on configured attempts."""
        retrying = retry(
            stop=stop_after_attempt(self.retry_attempts),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type((requests.RequestException, ConnectionError, TimeoutError)),
            reraise=True,
        )
        return retrying(self._fetch_raw)()

    def _make_request(self, url: str, **kwargs) -> requests.Response:
        """HTTP request with User-Agent rotation and timeout from config."""
        headers = kwargs.pop("headers", {})
        headers.setdefault("User-Agent", random.choice(USER_AGENTS))
        timeout = kwargs.pop("timeout", self.timeout)
        response = requests.get(url, headers=headers, timeout=timeout, **kwargs)
        response.raise_for_status()
        return response

    def _clean_html(self, html: str) -> str:
        """Strip HTML tags, normalize whitespace."""
        if not html:
            return ""
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()
        text = soup.get_text(strip=True)
        text = " ".join(text.split())
        return text[:500] if len(text) > 500 else text

    def _parse_date(self, date_str: str) -> datetime:
        """Parse various date formats to datetime.

        Supports RFC 2822, ISO 8601, and common Chinese date formats.
        """
        if not date_str:
            return datetime.now(tz=timezone.utc)

        date_str = date_str.strip()

        # RFC 2822 (e.g. "Tue, 04 Feb 2025 12:00:00 +0000")
        try:
            return parsedate_to_datetime(date_str)
        except Exception:
            pass

        # ISO 8601 variants
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            pass

        # Strptime formats including Chinese
        formats = [
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%Y年%m月%d日 %H:%M:%S",
            "%Y年%m月%d日 %H:%M",
            "%Y年%m月%d日",
            "%m月%d日 %H:%M",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue

        logger.warning(f"Could not parse date '{date_str}', using now()")
        return datetime.now(tz=timezone.utc)
