"""China Fetcher Base - RSSHub JSON-based fetchers for Chinese sources."""

from datetime import datetime, timezone
from typing import Any

from src.fetchers.base_fetcher import BaseFetcher
from src.models import NewsItem
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class RSSHubFetcher(BaseFetcher):
    """Base fetcher for Chinese sources via RSSHub JSON API."""

    def __init__(self, rsshub_url: str, source_name: str):
        super().__init__(source_name, source_type="china_news", language="zh")
        self.rsshub_url = rsshub_url

    def _fetch_raw(self) -> list[dict]:
        """Fetch JSON from RSSHub and extract items list."""
        response = self._make_request(
            self.rsshub_url,
            headers={"Accept": "application/json"},
        )
        data = response.json()
        if not data:
            return []

        if isinstance(data, dict) and "items" in data:
            return data["items"]
        if isinstance(data, dict):
            for key in ("items", "data", "results"):
                if key in data and isinstance(data[key], list):
                    return data[key]
            return []
        if isinstance(data, list):
            return data
        return []

    def _parse_item(self, raw_item: Any) -> NewsItem:
        """Parse a RSSHub JSON item into NewsItem."""
        item: dict = raw_item
        date_str = (
            item.get("date")
            or item.get("pubDate")
            or item.get("created_at")
            or ""
        )
        timestamp = self._parse_date(date_str)
        content = self._clean_html(
            item.get("description") or item.get("content") or ""
        )

        return NewsItem(
            title=item.get("title", "No title"),
            url=item.get("url", ""),
            source=self.source_name,
            timestamp=timestamp,
            content=content,
            source_type=self.source_type,
            language=self.language,
            metadata={
                k: v
                for k, v in item.items()
                if k not in ("title", "url", "description", "content",
                             "date", "pubDate", "created_at")
                and v is not None
            },
        )


class ChinaNewsFetcher(RSSHubFetcher):
    """Base fetcher for Chinese news sources."""

    def __init__(self, rsshub_url: str, source_name: str):
        super().__init__(rsshub_url, source_name)
