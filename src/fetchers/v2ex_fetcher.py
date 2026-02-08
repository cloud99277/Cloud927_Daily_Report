"""V2EX Fetcher using RSSHub JSON endpoint."""

import re
from datetime import datetime, timezone
from typing import Any

from src.fetchers.base_fetcher import BaseFetcher
from src.models import NewsItem
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class V2EXFetcher(BaseFetcher):
    """Fetch V2EX share posts via RSSHub JSON endpoint."""

    def __init__(self):
        super().__init__(source_name="v2ex", source_type="social", language="zh")
        self.api_url = "https://rsshub.app/v2ex/go/share"

    def _fetch_raw(self) -> list[dict]:
        """Fetch JSON from RSSHub and extract items."""
        resp = self._make_request(
            self.api_url,
            headers={"Accept": "application/json"},
        )
        data = resp.json()
        if not data:
            return []

        if isinstance(data, dict):
            for key in ("items", "posts", "data", "results"):
                if key in data and isinstance(data[key], list):
                    return data[key]
            return []
        if isinstance(data, list):
            return data
        return []

    def _parse_item(self, raw_item: Any) -> NewsItem:
        """Convert V2EX post dict into NewsItem."""
        post = raw_item
        title = post.get("title") or post.get("name", "")

        url = post.get("url") or post.get("link", "")
        if url and not url.startswith("http"):
            url = f"https://v2ex.com{url}"
        if not url:
            url = f"https://v2ex.com/t/{post.get('id', '')}"

        content = post.get("content") or post.get("description") or post.get("summary", "")
        content = re.sub(r"<[^>]+>", "", content)
        content = content[:300] if len(content) > 300 else content

        date_str = post.get("created_at") or post.get("pubDate") or post.get("date", "")
        if isinstance(date_str, (int, float)):
            timestamp = datetime.fromtimestamp(date_str, tz=timezone.utc)
        else:
            timestamp = self._parse_date(str(date_str))

        return NewsItem(
            title=title,
            url=url,
            source=self.source_name,
            timestamp=timestamp,
            content=content,
            source_type=self.source_type,
            language=self.language,
            metadata={
                "author": post.get("author") or post.get("user", ""),
                "node": post.get("node") or post.get("category", ""),
                "replies": post.get("replies", 0),
            },
        )
