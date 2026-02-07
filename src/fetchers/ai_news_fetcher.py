"""AI News API Fetcher for OpenAI, Anthropic, Google AI, Meta AI official sources."""
import json
import logging
from typing import Any

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# Mock data as fallback
MOCK_AI_NEWS = [
    {
        "title": "OpenAI announces GPT-4.5 with improved reasoning",
        "url": "https://openai.com/blog/gpt-4-5",
        "source": "OpenAI",
        "published_at": "2026-02-08",
        "summary": "OpenAI releases GPT-4.5 with enhanced reasoning capabilities and lower latency.",
        "category": "model",
    },
    {
        "title": "Anthropic releases Claude 3.7 with extended context",
        "url": "https://www.anthropic.com/news/claude-3-7",
        "source": "Anthropic",
        "published_at": "2026-02-07",
        "summary": "Claude 3.7 brings 200K context window and improved coding abilities.",
        "category": "model",
    },
    {
        "title": "Google DeepMind shares new reasoning techniques",
        "url": "https://deepmind.google/blog/new-reasoning",
        "source": "Google DeepMind",
        "published_at": "2026-02-06",
        "summary": "New AI reasoning techniques achieve state-of-the-art on math benchmarks.",
        "category": "research",
    },
]


class AINewsFetcher:
    """Fetch AI news from official company blogs and APIs."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.sources = [
            {
                "name": "OpenAI",
                "url": "https://openai.com/blog/",
                "type": "html",
                "selector": "article a[href*='/blog/']",
            },
            {
                "name": "Anthropic",
                "url": "https://www.anthropic.com/news",
                "type": "html",
                "selector": "article a[href*='/news/']",
            },
            {
                "name": "Google DeepMind",
                "url": "https://deepmind.google/blog",
                "type": "html",
                "selector": "article a[href*='/blog']",
            },
            {
                "name": "Meta AI",
                "url": "https://ai.meta.com/blog/",
                "type": "html",
                "selector": "article a[href*='/blog/']",
            },
        ]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_source(self, source: dict) -> list[dict]:
        """Fetch news from a single source."""
        try:
            headers = {
                "User-Agent": "Cloud927-Daily-Report/2.0",
            }
            response = requests.get(source["url"], timeout=self.timeout, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            items = []

            for elem in soup.select(source["selector"])[:5]:
                try:
                    title_elem = elem.find(string=True, recursive=False) or elem.find("h2") or elem.find("h3")
                    title = title_elem.strip() if title_elem else elem.get_text(strip=True)

                    href = elem.get("href", "")
                    if href and not href.startswith("http"):
                        if href.startswith("/"):
                            base_url = source["url"].split("/blog")[0]
                            href = base_url + href
                        else:
                            href = source["url"].rstrip("/") + "/" + href.lstrip("/")

                    if title and len(title) > 10:
                        items.append({
                            "title": title,
                            "url": href if href.startswith("http") else source["url"],
                            "source": source["name"],
                            "category": source["name"],
                        })
                except Exception:
                    continue

            return items

        except Exception as e:
            logger.debug(f"Failed to fetch {source['name']}: {e}")
            return []

    def fetch(self) -> list[dict[str, Any]]:
        """Fetch AI news from all sources."""
        logger.info("Starting AI news fetch")

        all_news = []
        for source in self.sources:
            items = self._fetch_source(source)
            all_news.extend(items)
            logger.info(f"Fetched {len(items)} items from {source['name']}")

        if not all_news:
            logger.warning("No AI news found, using mock data")
            return MOCK_AI_NEWS

        # Sort by source priority and limit
        priority_order = {"OpenAI": 1, "Anthropic": 2, "Google DeepMind": 3, "Meta AI": 4}
        all_news.sort(key=lambda x: priority_order.get(x.get("source", ""), 5))

        return all_news[:10]

    def to_json(self) -> str:
        """Return news as JSON string."""
        return json.dumps(self.fetch(), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    fetcher = AINewsFetcher()
    print(fetcher.to_json())
