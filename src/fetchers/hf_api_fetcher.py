"""HuggingFace API Fetcher for daily papers."""

from datetime import datetime, timezone
from typing import Any

from src.fetchers.base_fetcher import BaseFetcher
from src.models import NewsItem
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class HuggingFaceAPIFetcher(BaseFetcher):
    """Fetch daily papers from HuggingFace JSON API."""

    def __init__(self):
        super().__init__(source_name="hf", source_type="paper", language="en")
        self.api_url = "https://huggingface.co/api/daily_papers"

    def _fetch_raw(self) -> list[dict]:
        """Fetch papers JSON from HF API."""
        resp = self._make_request(
            self.api_url,
            headers={"Accept": "application/json"},
        )
        data = resp.json()
        if not data:
            return []

        if isinstance(data, dict):
            for key in ("papers", "daily_papers", "items", "results"):
                if key in data and isinstance(data[key], list):
                    return data[key]
            for value in data.values():
                if isinstance(value, list):
                    return value
            return []

        if isinstance(data, list):
            return data
        return []

    def _parse_item(self, raw_item: Any) -> NewsItem:
        """Parse HF paper dict into NewsItem."""
        paper = raw_item
        title = paper.get("title") or paper.get("name", "Unknown Paper")
        abstract = (
            paper.get("abstract")
            or paper.get("description")
            or paper.get("summary", "")
        )

        paper_id = paper.get("id") or paper.get("paperId")
        if paper_id:
            url = f"https://huggingface.co/papers/{paper_id}"
        else:
            url = paper.get("url", "https://huggingface.co/papers")

        tags = paper.get("tags", [])
        if isinstance(tags, str):
            tags = [tags] if tags else []

        return NewsItem(
            title=title,
            url=url,
            source=self.source_name,
            timestamp=datetime.now(tz=timezone.utc),
            content=abstract[:500] if len(abstract) > 500 else abstract,
            source_type=self.source_type,
            language=self.language,
            metadata={"tags": tags[:5]},
        )
