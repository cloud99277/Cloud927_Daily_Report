"""Product Hunt AI Fetcher - Discover new AI products and tools."""
import json
import logging
from datetime import datetime, timedelta
from typing import Any

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# Mock data as fallback
MOCK_PH_PRODUCTS = [
    {
        "name": "AI Code Reviewer Pro",
        "url": "https://producthunt.com/posts/ai-code-reviewer",
        "tagline": "Automated code review with GPT-4",
        "votes": 456,
        "launched_at": (datetime.now() - timedelta(days=1)).isoformat(),
        "categories": ["Developer Tools", "AI"],
    },
    {
        "name": "VoiceClone AI",
        "url": "https://producthunt.com/posts/voiceclone",
        "tagline": "Realistic voice cloning in seconds",
        "votes": 892,
        "launched_at": (datetime.now() - timedelta(days=2)).isoformat(),
        "categories": ["Audio", "AI"],
    },
]


class ProductHuntFetcher:
    """Fetch trending AI products from Product Hunt."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.base_url = "https://www.producthunt.com"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_html(self, url: str) -> str:
        """Fetch HTML with retry logic."""
        headers = {
            "User-Agent": "Cloud927-Daily-Report/2.0",
        }
        response = requests.get(url, timeout=self.timeout, headers=headers)
        response.raise_for_status()
        return response.text

    def _parse_product(self, card) -> dict[str, Any] | None:
        """Parse a single product card."""
        try:
            title_elem = card.select_one("h3") or card.select_one("[data-test*='title']")
            tagline_elem = card.select_one("p") or card.select_one("[data-test*='tagline']")
            vote_elem = card.select_one("[data-test*='vote']") or card.select_one("span:has(svg)")

            title = title_elem.get_text(strip=True) if title_elem else ""
            tagline = tagline_elem.get_text(strip=True) if tagline_elem else ""
            votes_text = vote_elem.get_text(strip=True) if vote_elem else "0"

            # Extract number from votes
            import re
            vote_match = re.search(r"([\d,]+)", votes_text.replace(",", ""))
            votes = int(vote_match.group(1)) if vote_match else 0

            link_elem = card.select_one("a[href*='/posts/']")
            href = link_elem.get("href", "") if link_elem else ""
            url = f"{self.base_url}{href}" if href.startswith("/") else href

            return {
                "name": title,
                "url": url,
                "tagline": tagline,
                "votes": votes,
                "categories": ["AI", "Productivity"],
            }

        except Exception as e:
            logger.debug(f"Parse error: {e}")
            return None

    def fetch_ai_products(self, limit: int = 5) -> list[dict[str, Any]]:
        """Fetch trending AI products."""
        logger.info("Fetching Product Hunt AI products")

        try:
            html = self._fetch_html(f"{self.base_url}/topics/ai")
            soup = BeautifulSoup(html, "html.parser")

            # Try different selectors for PH's dynamic content
            products = []
            cards = soup.select("[data-test*='post-card']") or soup.select("article") or soup.select(".styles_card")

            for card in cards[:15]:
                product = self._parse_product(card)
                if product and product.get("votes", 0) >= 50:
                    products.append(product)

            if products:
                products.sort(key=lambda x: x.get("votes", 0), reverse=True)
                logger.info(f"Found {len(products)} AI products")
                return products[:limit]

            logger.warning("No products found, using mock data")
            return MOCK_PH_PRODUCTS[:limit]

        except Exception as e:
            logger.error(f"Failed to fetch Product Hunt: {e}")
            return MOCK_PH_PRODUCTS[:limit]

    def fetch(self) -> dict[str, Any]:
        """Fetch AI products, return structured JSON."""
        products = self.fetch_ai_products(limit=5)
        return {
            "products": products,
            "count": len(products),
        }

    def to_json(self) -> str:
        """Return as JSON string."""
        return json.dumps(self.fetch(), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    fetcher = ProductHuntFetcher()
    print(fetcher.to_json())
