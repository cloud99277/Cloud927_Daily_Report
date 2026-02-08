"""Product Hunt AI Fetcher."""

import re
from datetime import datetime, timezone
from typing import Any

from bs4 import BeautifulSoup

from src.fetchers.base_fetcher import BaseFetcher
from src.models import NewsItem
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ProductHuntFetcher(BaseFetcher):
    """Fetch trending AI products from Product Hunt."""

    def __init__(self):
        super().__init__(source_name="ph", source_type="tech", language="en")
        self.base_url = "https://www.producthunt.com"

    def _fetch_raw(self) -> list[dict]:
        """Fetch AI product cards from Product Hunt."""
        resp = self._make_request(f"{self.base_url}/topics/ai")
        soup = BeautifulSoup(resp.text, "html.parser")

        products = []
        cards = (
            soup.select("[data-test*='post-card']")
            or soup.select("article")
            or soup.select(".styles_card")
        )

        for card in cards[:15]:
            product = self._parse_card(card)
            if product and product.get("votes", 0) >= 50:
                products.append(product)

        products.sort(key=lambda x: x.get("votes", 0), reverse=True)
        return products

    def _parse_card(self, card: Any) -> dict | None:
        """Parse a single product card element."""
        try:
            title_elem = card.select_one("h3") or card.select_one("[data-test*='title']")
            tagline_elem = card.select_one("p") or card.select_one("[data-test*='tagline']")
            vote_elem = card.select_one("[data-test*='vote']") or card.select_one("span:has(svg)")

            title = title_elem.get_text(strip=True) if title_elem else ""
            tagline = tagline_elem.get_text(strip=True) if tagline_elem else ""
            votes_text = vote_elem.get_text(strip=True) if vote_elem else "0"

            vote_match = re.search(r"([\d,]+)", votes_text.replace(",", ""))
            votes = int(vote_match.group(1)) if vote_match else 0

            link_elem = card.select_one("a[href*='/posts/']")
            href = link_elem.get("href", "") if link_elem else ""
            url = f"{self.base_url}{href}" if href.startswith("/") else href

            return {
                "title": title,
                "url": url,
                "tagline": tagline,
                "votes": votes,
            }
        except Exception as e:
            logger.debug(f"Parse error: {e}")
            return None

    def _parse_item(self, raw_item: Any) -> NewsItem:
        """Convert product dict into NewsItem."""
        product = raw_item
        return NewsItem(
            title=product.get("title", ""),
            url=product.get("url", ""),
            source=self.source_name,
            timestamp=datetime.now(tz=timezone.utc),
            content=product.get("tagline", ""),
            score=float(product.get("votes", 0)),
            source_type=self.source_type,
            language=self.language,
        )
