"""Base RSS Fetcher for news sources."""

import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class BaseRSSFetcher(ABC):
    """Base class for RSS-based fetchers."""

    def __init__(
        self,
        rss_url: str,
        source_name: str,
        timeout: int = 30,
        retry_attempts: int = 3
    ):
        """
        Initialize the RSS fetcher.

        Args:
            rss_url: URL of the RSS feed
            source_name: Name of the source
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts
        """
        self.rss_url = rss_url
        self.source_name = source_name
        self.timeout = timeout
        self.retry_attempts = retry_attempts

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _fetch_rss(self) -> dict | None:
        """Fetch RSS feed with retry logic."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
        }

        response = requests.get(self.rss_url, timeout=self.timeout, headers=headers)
        response.raise_for_status()
        return response.text

    def _parse_rss_date(self, date_str: str) -> int:
        """Parse various date formats to Unix timestamp."""
        if not date_str:
            return int(time.time())

        date_formats = [
            "%a, %d %b %Y %H:%M:%S %z",  # RFC 2822
            "%a, %d %b %Y %H:%M:%S %Z",  # RFC 2822 (no timezone)
            "%Y-%m-%dT%H:%M:%SZ",         # ISO 8601
            "%Y-%m-%dT%H:%M:%S%z",       # ISO 8601 with timezone
            "%Y-%m-%d %H:%M:%S",         # MySQL format
            "%Y-%m-%d",                   # Simple date
        ]

        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return int(dt.timestamp())
            except ValueError:
                continue

        return int(time.time())

    def _extract_image(self, soup: BeautifulSoup) -> str | None:
        """Extract image URL from RSS item."""
        # Try enclosure
        enclosure = soup.find("enclosure")
        if enclosure and enclosure.get("type", "").startswith("image"):
            return enclosure.get("url")

        # Try media:thumbnail
        media = soup.find("media:thumbnail") or soup.find("thumbnail")
        if media:
            return media.get("url")

        # Try content:encoded
        content = soup.find("content:encoded") or soup.find("description")
        if content:
            img = BeautifulSoup(content.get_text(), "html.parser").find("img")
            if img:
                return img.get("src")

        return None

    def _clean_html(self, html: str) -> str:
        """Clean HTML content and extract text."""
        if not html:
            return ""

        soup = BeautifulSoup(html, "html.parser")

        # Remove scripts and styles
        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()

        # Get text
        text = soup.get_text(strip=True)

        # Normalize whitespace
        text = " ".join(text.split())

        return text[:500] if len(text) > 500 else text

    @abstractmethod
    def _parse_item(self, item: BeautifulSoup, item_data: dict) -> dict:
        """Parse individual RSS item. Must be implemented by subclasses."""
        pass

    def _parse_feed(self, xml_content: str) -> list[dict]:
        """Parse RSS/Atom feed content."""
        from xml.etree import ElementTree as ET

        soup = BeautifulSoup(xml_content, "xml")
        items = []

        # Find all item entries
        for entry in soup.find_all(["item", "entry"]):
            item_data = {}

            # Basic fields
            title = entry.find("title")
            item_data["title"] = title.get_text() if title else "No title"

            link = entry.find("link")
            if link:
                item_data["url"] = link.get_text() if link.name == "link" else link.get("href")
            else:
                link_tag = entry.find("link", href=True)
                if link_tag:
                    item_data["url"] = link_tag.get("href")

            description = entry.find("description") or entry.find("summary")
            if description:
                item_data["content"] = self._clean_html(description.get_text())
                item_data["description"] = description.get_text()[:300]

            # Date
            pub_date = entry.find(["pubDate", "published", "dc:date"])
            if pub_date:
                item_data["timestamp"] = self._parse_rss_date(pub_date.get_text())
                item_data["published_at"] = pub_date.get_text()

            # Author
            author = entry.find("author") or entry.find("dc:creator")
            if author:
                item_data["author"] = author.get_text()

            # Categories
            categories = entry.find_all("category")
            if categories:
                item_data["categories"] = [c.get_text() for c in categories]

            # GUID
            guid = entry.find("guid") or entry.find("id")
            if guid:
                item_data["guid"] = guid.get_text()

            # Image
            item_data["image"] = self._extract_image(entry)

            # Source
            item_data["source"] = self.source_name

            # Parse with subclass method
            parsed_item = self._parse_item(entry, item_data)
            items.append(parsed_item)

        return items

    def fetch(self, limit: int = 20) -> list[dict]:
        """
        Fetch and parse RSS feed.

        Args:
            limit: Maximum number of items to return

        Returns:
            List of parsed items
        """
        logger.info(f"Fetching RSS feed: {self.source_name}")

        try:
            xml_content = self._fetch_rss()
            items = self._parse_feed(xml_content)

            # Apply limit
            items = items[:limit]

            logger.info(f"Fetched {len(items)} items from {self.source_name}")
            return items

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch {self.source_name}: {e}")
            return self._get_mock_data()
        except Exception as e:
            logger.error(f"Failed to fetch {self.source_name}: {e}")
            return self._get_mock_data()

    def _get_mock_data(self) -> list[dict]:
        """Return mock data when fetch fails."""
        logger.warning(f"Using mock data for {self.source_name}")
        current_time = int(time.time())

        return [
            {
                "title": f"【{self.source_name}】示例新闻标题 - {datetime.now().strftime('%H:%M')}",
                "url": f"https://example.com/{self.source_name.lower()}",
                "source": self.source_name,
                "timestamp": current_time,
                "content": "这是模拟数据，当RSS源无法访问时使用。",
                "categories": ["News"],
            }
        ]
