"""Hugging Face daily papers fetcher."""
import json
import logging
from typing import Any

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# Mock data as fallback
MOCK_PAPERS = [
    {
        "name": "Llama 3: The Future of Open LLMs",
        "abstract": "This paper introduces Llama 3, a state-of-the-art open language model with improved reasoning and multilingual capabilities. The model achieves competitive performance with closed-source alternatives while remaining open for research use.",
        "url": "https://huggingface.co/papers/llama3",
        "tags": ["llm", "transformer", "multilingual"],
    },
    {
        "name": "Stable Diffusion 3: Improved Text-to-Image",
        "abstract": "A novel diffusion model architecture that significantly improves text understanding and image quality. Uses a multimodal transformer backbone for better alignment between text and image representations.",
        "url": "https://huggingface.co/papers/sd3",
        "tags": ["diffusion", "vision", "multimodal"],
    },
    {
        "name": "Efficient Vision Transformers Survey",
        "abstract": "A comprehensive survey of methods to improve the efficiency of Vision Transformers, including pruning, quantization, and architectural innovations. Covers recent advances in making ViTs practical for edge deployment.",
        "url": "https://huggingface.co/papers/efficient-vits",
        "tags": ["vision", "efficiency", "survey"],
    },
]


class HuggingFaceFetcher:
    """Fetch daily papers from Hugging Face."""

    def __init__(self):
        self.base_url = "https://huggingface.co/papers"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_html(self) -> str:
        """Fetch HTML page with retry logic."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(self.base_url, timeout=30, headers=headers)
        response.raise_for_status()
        return response.text

    def fetch(self) -> list[dict[str, Any]]:
        """Fetch daily papers from Hugging Face papers page."""
        logger.info("Starting HF papers fetch")

        try:
            html = self._fetch_html()
            soup = BeautifulSoup(html, "html.parser")

            papers = []
            # Find paper cards on the page
            paper_cards = soup.select("article") or soup.select(".paper-card") or soup.select("[data-target='PaperCard']")

            for card in paper_cards[:5]:
                paper = self._parse_paper_card(card)
                if paper:
                    papers.append(paper)

            if papers:
                logger.info(f"Fetched {len(papers)} papers from HTML")
                return papers[:3]  # Return top 3

            # If no papers found from HTML parsing, use mock data
            logger.warning("No papers parsed from HTML, using mock data")
            return MOCK_PAPERS

        except Exception as e:
            logger.error(f"Failed to fetch HF papers: {e}, using mock data")
            return MOCK_PAPERS

    def _parse_paper_card(self, card) -> dict[str, Any] | None:
        """Parse a paper card element into structured data."""
        try:
            # Try to find title
            title_elem = card.select_one("h3") or card.select_one("h2") or card.select_one(".title") or card.select_one("a")
            title = title_elem.get_text(strip=True) if title_elem else "Unknown Paper"

            # Try to find link
            link_elem = card.select_one("a")
            url = ""
            if link_elem and link_elem.get("href"):
                href = link_elem.get("href")
                url = f"https://huggingface.co{href}" if href.startswith("/") else href

            # Try to find abstract/description
            abstract_elem = card.select_one("p") or card.select_one(".description") or card.select_one(".abstract")
            abstract = abstract_elem.get_text(strip=True) if abstract_elem else "No abstract available"
            if len(abstract) > 500:
                abstract = abstract[:497] + "..."

            # Try to find tags
            tags = []
            tag_elems = card.select(".tag") or card.select("[data-target='Tag']")
            for tag_elem in tag_elems:
                tag_text = tag_elem.get_text(strip=True)
                if tag_text:
                    tags.append(tag_text)

            return {
                "name": title,
                "abstract": abstract,
                "url": url or "https://huggingface.co/papers",
                "tags": tags,
            }
        except Exception as e:
            logger.debug(f"Failed to parse paper card: {e}")
            return None

    def to_json(self) -> str:
        """Return papers as JSON string."""
        return json.dumps(self.fetch(), ensure_ascii=False, indent=2)
