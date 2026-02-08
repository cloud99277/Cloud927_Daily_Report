"""ArXiv Paper Fetcher via API."""

import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode

from bs4 import BeautifulSoup

from src.fetchers.base_fetcher import BaseFetcher
from src.models import NewsItem
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ArxivFetcher(BaseFetcher):
    """Fetch AI papers from ArXiv API."""

    ARXIV_API = "http://export.arxiv.org/api/query"

    AI_CATEGORIES = [
        "cs.AI",
        "cs.LG",
        "cs.CL",
        "cs.NE",
        "stat.ML",
    ]

    def __init__(self):
        super().__init__(source_name="arxiv", source_type="paper", language="en")

    def _fetch_raw(self) -> list[dict]:
        """Query ArXiv API and parse XML entries."""
        cat_query = " OR ".join(f"cat:{cat}" for cat in self.AI_CATEGORIES)
        query = (
            f"({cat_query}) AND "
            f"(ti:AI OR ti:\"machine learning\" OR ti:NLP OR "
            f"ti:\"deep learning\" OR abs:AI OR abs:\"machine learning\")"
        )

        params = {
            "search_query": query,
            "max_results": 30,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "start": 0,
        }

        url = f"{self.ARXIV_API}?{urlencode(params)}"
        resp = self._make_request(
            url,
            headers={"Accept": "application/atom+xml"},
            timeout=60,
        )

        soup = BeautifulSoup(resp.text, "xml")
        entries = []
        cutoff = int(time.time()) - (7 * 86400)

        for entry in soup.find_all("entry"):
            parsed = self._parse_entry_xml(entry)
            if parsed.get("timestamp", 0) >= cutoff:
                entries.append(parsed)

        return entries

    def _parse_entry_xml(self, entry: Any) -> dict:
        """Extract fields from a single ArXiv XML entry."""
        title_tag = entry.find("title")
        title = title_tag.get_text().replace("\n", " ").strip() if title_tag else "No title"

        summary_tag = entry.find("summary")
        abstract = summary_tag.get_text().replace("\n", " ").strip() if summary_tag else ""

        # Links
        pdf_url = ""
        html_url = ""
        for link in entry.find_all("link"):
            href = link.get("href", "")
            if "pdf" in href:
                pdf_url = href
            elif href:
                html_url = href

        published = entry.find("published")
        timestamp = int(time.time())
        if published:
            try:
                dt = datetime.strptime(
                    published.get_text().replace("Z", "+00:00"),
                    "%Y-%m-%dT%H:%M:%S%z",
                )
                timestamp = int(dt.timestamp())
            except ValueError:
                pass

        authors = [
            name.get_text()
            for author in entry.find_all("author")
            if (name := author.find("name"))
        ][:5]

        categories = [
            cat.get("term")
            for cat in entry.find_all("category")
            if cat.get("term")
        ]

        return {
            "title": title,
            "abstract": abstract[:500],
            "url": html_url or pdf_url,
            "pdf_url": pdf_url,
            "authors": authors,
            "categories": categories,
            "timestamp": timestamp,
        }

    def _parse_item(self, raw_item: Any) -> NewsItem:
        """Convert parsed ArXiv entry dict into NewsItem."""
        entry = raw_item
        ts = entry.get("timestamp", 0)
        timestamp = (
            datetime.fromtimestamp(ts, tz=timezone.utc)
            if ts
            else datetime.now(tz=timezone.utc)
        )

        return NewsItem(
            title=entry.get("title", ""),
            url=entry.get("url", ""),
            source=self.source_name,
            timestamp=timestamp,
            content=entry.get("abstract", ""),
            source_type=self.source_type,
            language=self.language,
            metadata={
                "authors": entry.get("authors", []),
                "categories": entry.get("categories", []),
                "pdf_url": entry.get("pdf_url", ""),
            },
        )
