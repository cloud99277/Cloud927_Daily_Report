"""RSS-based fetcher built on BaseFetcher."""

from datetime import datetime, timezone
from typing import Any

from bs4 import BeautifulSoup

from src.fetchers.base_fetcher import BaseFetcher
from src.models import NewsItem
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class RSSFetcher(BaseFetcher):
    """Base for RSS/Atom feed fetchers."""

    def __init__(
        self,
        rss_url: str,
        source_name: str,
        source_type: str = "",
        language: str = "en",
    ):
        super().__init__(source_name, source_type, language)
        self.rss_url = rss_url

    def _fetch_raw(self) -> list[dict]:
        """Fetch RSS XML and return parsed entry dicts."""
        response = self._make_request(
            self.rss_url,
            headers={"Accept": "application/rss+xml, application/xml, text/xml, */*"},
        )
        return self._parse_feed(response.text)

    def _parse_item(self, raw_item: Any) -> NewsItem:
        """Convert a parsed RSS entry dict into a NewsItem."""
        entry: dict = raw_item
        timestamp = self._parse_date(entry.get("pub_date", ""))

        return NewsItem(
            title=entry.get("title", "No title"),
            url=entry.get("url", ""),
            source=self.source_name,
            timestamp=timestamp,
            content=entry.get("content", ""),
            source_type=self.source_type,
            language=self.language,
            metadata={
                k: v
                for k, v in entry.items()
                if k not in ("title", "url", "content", "pub_date")
                and v is not None
            },
        )

    # ------------------------------------------------------------------
    # RSS/Atom XML parsing
    # ------------------------------------------------------------------

    def _parse_feed(self, xml_content: str) -> list[dict]:
        """Parse RSS/Atom XML into a list of entry dicts."""
        soup = BeautifulSoup(xml_content, "xml")
        entries: list[dict] = []

        for entry in soup.find_all(["item", "entry"]):
            data = self._parse_entry(entry)
            data["source"] = self.source_name
            entries.append(data)

        return entries

    def _parse_entry(self, entry: BeautifulSoup) -> dict:
        """Extract fields from a single RSS/Atom entry element."""
        data: dict[str, Any] = {}

        # Title
        title_tag = entry.find("title")
        data["title"] = title_tag.get_text(strip=True) if title_tag else "No title"

        # Link
        data["url"] = self._extract_link(entry)

        # Description / content
        desc = entry.find("description") or entry.find("summary")
        if desc:
            data["content"] = self._clean_html(desc.get_text())

        # Date
        pub_date = entry.find(["pubDate", "published", "dc:date", "updated"])
        if pub_date:
            data["pub_date"] = pub_date.get_text(strip=True)

        # Author
        author = entry.find("author") or entry.find("dc:creator")
        if author:
            data["author"] = author.get_text(strip=True)

        # Categories
        categories = entry.find_all("category")
        if categories:
            data["categories"] = [c.get_text(strip=True) for c in categories]

        # GUID
        guid = entry.find("guid") or entry.find("id")
        if guid:
            data["guid"] = guid.get_text(strip=True)

        # Image
        image = self._extract_image(entry)
        if image:
            data["image"] = image

        return data

    @staticmethod
    def _extract_link(entry: BeautifulSoup) -> str:
        """Extract the best link from an RSS/Atom entry."""
        link = entry.find("link")
        if link:
            href = link.get("href")
            if href:
                return href
            text = link.get_text(strip=True)
            if text:
                return text
        return ""

    @staticmethod
    def _extract_image(entry: BeautifulSoup) -> str | None:
        """Extract image URL from an RSS entry."""
        enclosure = entry.find("enclosure")
        if enclosure and enclosure.get("type", "").startswith("image"):
            return enclosure.get("url")

        media = entry.find("media:thumbnail") or entry.find("thumbnail")
        if media:
            return media.get("url")

        content = entry.find("content:encoded") or entry.find("description")
        if content:
            img = BeautifulSoup(content.get_text(), "html.parser").find("img")
            if img:
                return img.get("src")

        return None
