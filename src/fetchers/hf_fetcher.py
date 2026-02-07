"""Hugging Face daily papers fetcher."""
import json
import logging
from typing import Any

import feedparser
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class HuggingFaceFetcher:
    """Fetch daily papers from Hugging Face."""

    def __init__(self):
        self.base_url = "https://huggingface.co/explore/rss"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_feed(self) -> str:
        """Fetch RSS feed with retry logic."""
        response = requests.get(self.base_url, timeout=30)
        response.raise_for_status()
        return response.text

    def fetch(self) -> list[dict[str, Any]]:
        """Fetch daily papers from Hugging Face RSS feed."""
        logger.info("Starting HF papers fetch")
        feed_text = self._fetch_feed()
        feed = feedparser.parse(feed_text)

        papers = []
        for entry in feed.entries[:3]:
            abstract = entry.get("summary", "") or entry.get("description", "")
            if len(abstract) > 500:
                abstract = abstract[:497] + "..."

            # Extract tags from categories if available
            tags = []
            if hasattr(entry, "tags"):
                for tag in entry.tags:
                    if tag.term:
                        tags.append(tag.term)

            papers.append({
                "title": entry.get("title", ""),
                "abstract": abstract,
                "url": entry.get("link", ""),
                "tags": tags,
            })

        logger.info(f"Fetched {len(papers)} papers")
        return papers

    def to_json(self) -> str:
        """Return papers as JSON string."""
        return json.dumps(self.fetch(), ensure_ascii=False, indent=2)
