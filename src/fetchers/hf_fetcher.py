"""Hugging Face daily papers fetcher (HTML scraping fallback)."""

from datetime import datetime, timezone
from typing import Any

from bs4 import BeautifulSoup

from src.fetchers.base_fetcher import BaseFetcher
from src.models import NewsItem
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class HuggingFaceFetcher(BaseFetcher):
    """Fetch daily papers from Hugging Face papers page via HTML."""

    def __init__(self):
        super().__init__(source_name="hf", source_type="paper", language="en")
        self.base_url = "https://huggingface.co/papers"

    def _fetch_raw(self) -> list[dict]:
        """Fetch and parse paper cards from HF papers page."""
        resp = self._make_request(self.base_url)
        soup = BeautifulSoup(resp.text, "html.parser")

        cards = (
            soup.select("article")
            or soup.select(".paper-card")
            or soup.select("[data-target='PaperCard']")
        )

        papers = []
        for card in cards[:5]:
            parsed = self._parse_card(card)
            if parsed:
                papers.append(parsed)
        return papers

    def _parse_card(self, card: Any) -> dict | None:
        """Parse a paper card element."""
        try:
            title_elem = (
                card.select_one("h3")
                or card.select_one("h2")
                or card.select_one(".title")
                or card.select_one("a")
            )
            title = title_elem.get_text(strip=True) if title_elem else "Unknown Paper"

            link_elem = card.select_one("a")
            url = ""
            if link_elem and link_elem.get("href"):
                href = link_elem.get("href")
                url = f"https://huggingface.co{href}" if href.startswith("/") else href

            abstract_elem = (
                card.select_one("p")
                or card.select_one(".description")
                or card.select_one(".abstract")
            )
            abstract = abstract_elem.get_text(strip=True) if abstract_elem else ""

            tags = [
                t.get_text(strip=True)
                for t in (card.select(".tag") or card.select("[data-target='Tag']"))
                if t.get_text(strip=True)
            ]

            return {
                "title": title,
                "abstract": abstract[:500],
                "url": url or "https://huggingface.co/papers",
                "tags": tags,
            }
        except Exception as e:
            logger.debug(f"Failed to parse paper card: {e}")
            return None

    def _parse_item(self, raw_item: Any) -> NewsItem:
        """Convert parsed paper dict into NewsItem."""
        paper = raw_item
        return NewsItem(
            title=paper.get("title", ""),
            url=paper.get("url", ""),
            source=self.source_name,
            timestamp=datetime.now(tz=timezone.utc),
            content=paper.get("abstract", ""),
            source_type=self.source_type,
            language=self.language,
            metadata={"tags": paper.get("tags", [])},
        )
