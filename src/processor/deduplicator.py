"""Deduplicator for cross-source content deduplication."""

import hashlib
import logging
import re
from difflib import SequenceMatcher
from typing import Any

logger = logging.getLogger(__name__)


class Deduplicator:
    """
    Cross-source content deduplication using:
    1. Exact title matching
    2. Fuzzy matching with similarity threshold
    3. Source priority rules
    """

    def __init__(
        self,
        exact_match_threshold: float = 0.95,
        fuzzy_match_threshold: float = 0.80,
        source_priority: dict[str, int] | None = None,
    ):
        """
        Initialize the deduplicator.

        Args:
            exact_match_threshold: Threshold for exact match (0-1)
            fuzzy_match_threshold: Threshold for fuzzy match (0-1)
            source_priority: Dict mapping source names to priority (higher = more trusted)
        """
        self.exact_match_threshold = exact_match_threshold
        self.fuzzy_match_threshold = fuzzy_match_threshold
        self.source_priority = source_priority or self._default_priority()

    def _default_priority(self) -> dict[str, int]:
        """Default source priority (higher = more trusted)."""
        return {
            # Official sources - highest priority
            "arxiv.org": 100,
            "openai.com": 95,
            "anthropic.com": 95,
            "google.com": 90,
            "meta.com": 90,
            # News sources
            "reuters.com": 85,
            "apnews.com": 85,
            "bbc.com": 80,
            "thepaper.cn": 80,
            "caixin.com": 80,
            # Tech platforms
            "github.com": 75,
            "huggingface.co": 75,
            "36kr.com": 70,
            "jiqizhixin.com": 70,
            # Social platforms - lower priority
            "reddit.com": 50,
            "v2ex.com": 50,
            "twitter.com": 45,
            "hn": 40,
        }

    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison."""
        if not title:
            return ""
        # Convert to lowercase, remove special characters
        title = title.lower().strip()
        title = re.sub(r"[^\w\s]", "", title)
        title = re.sub(r"\s+", " ", title)
        return title

    def _calculate_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two titles."""
        normalized1 = self._normalize_title(title1)
        normalized2 = self._normalize_title(title2)
        return SequenceMatcher(None, normalized1, normalized2).ratio()

    def _get_source_priority(self, item: dict) -> int:
        """Get the priority score for an item based on its source."""
        url = item.get("url", "") or item.get("source", "") or ""
        source_name = item.get("source", "") or ""

        # Check URL domain
        for domain, priority in self.source_priority.items():
            if domain in url.lower():
                return priority

        # Check explicit source name
        if source_name in self.source_priority:
            return self.source_priority[source_name]

        return 50  # Default priority

    def _create_fingerprint(self, item: dict) -> str:
        """Create a simple fingerprint for an item."""
        title = self._normalize_title(item.get("title", ""))
        url = item.get("url", "")

        # Create hash from title and URL
        content = f"{title}:{url}"
        return hashlib.md5(content.encode()).hexdigest()

    def deduplicate(
        self,
        items: list[dict],
        group_by_source: bool = False
    ) -> list[dict]:
        """
        Deduplicate a list of items.

        Args:
            items: List of items with 'title' and 'url' fields
            group_by_source: If True, only deduplicate within same source

        Returns:
            Deduplicated list of items
        """
        if not items:
            return []

        logger.info(f"Deduplicating {len(items)} items")
        seen_fingerprints = set()
        seen_titles = {}
        results = []

        # Sort by priority first (higher priority sources first)
        sorted_items = sorted(
            items,
            key=lambda x: (self._get_source_priority(x), x.get("timestamp", 0)),
            reverse=True
        )

        for item in sorted_items:
            title = item.get("title", "")
            url = item.get("url", "")
            source = item.get("source", "unknown")

            # Skip if already seen
            fingerprint = self._create_fingerprint(item)
            if fingerprint in seen_fingerprints:
                logger.debug(f"Skipping duplicate (fingerprint): {title[:50]}...")
                continue

            # Check for similar titles
            is_duplicate = False
            for seen_title, seen_source in seen_titles.items():
                similarity = self._calculate_similarity(title, seen_title)

                if similarity >= self.exact_match_threshold:
                    # Exact match - always skip
                    is_duplicate = True
                    logger.debug(f"Skipping exact duplicate: {title[:50]}...")
                    break
                elif similarity >= self.fuzzy_match_threshold:
                    # Fuzzy match - check if we should keep this one
                    if group_by_source and source == seen_source:
                        is_duplicate = True
                        logger.debug(f"Skipping same-source duplicate: {title[:50]}...")
                        break
                    elif self._get_source_priority(item) > self.source_priority.get(seen_source, 50):
                        # Higher priority source - replace the old one
                        logger.debug(f"Replacing lower priority duplicate: {seen_title[:50]}...")
                        seen_titles.pop(seen_title)
                        if fingerprint not in seen_fingerprints:
                            break
                    else:
                        is_duplicate = True
                        logger.debug(f"Skipping fuzzy duplicate: {title[:50]}...")
                        break

            if is_duplicate:
                continue

            # Add to results
            seen_fingerprints.add(fingerprint)
            seen_titles[title] = source
            results.append(item)

        logger.info(f"Deduplication complete: {len(items)} -> {len(results)} items")
        return results

    def deduplicate_by_source(self, items_by_source: dict[str, list[dict]]) -> dict[str, list[dict]]:
        """
        Deduplicate items grouped by source.

        Args:
            items_by_source: Dict mapping source names to lists of items

        Returns:
            Dict with deduplicated items per source
        """
        results = {}
        for source, items in items_by_source.items():
            results[source] = self.deduplicate(items, group_by_source=True)
        return results

    def merge_duplicates(
        self,
        items: list[dict]
    ) -> list[dict]:
        """
        Merge duplicate items keeping metadata from all sources.

        Args:
            items: List of potentially duplicate items

        Returns:
            List with merged duplicates grouped together
        """
        if not items:
            return []

        # First deduplicate
        unique_items = self.deduplicate(items)

        # Group items that are similar but from different sources
        clusters = {}
        for item in unique_items:
            title = item.get("title", "")
            best_match = None
            best_score = 0

            for key, cluster in clusters.items():
                score = self._calculate_similarity(title, key)
                if score > best_score and score >= self.fuzzy_match_threshold:
                    best_score = score
                    best_match = key

            if best_match:
                clusters[best_match].append(item)
            else:
                clusters[title] = [item]

        return [
            {
                **cluster[0],
                "merged_sources": list(set(item.get("source", "unknown") for item in cluster)),
                "merged_count": len(cluster),
            }
            for cluster in clusters.values()
        ]


if __name__ == "__main__":
    # Test deduplication
    deduplicator = Deduplicator()

    test_items = [
        {"title": "OpenAI releases GPT-4", "url": "https://openai.com/gpt4", "source": "openai.com", "timestamp": 1000},
        {"title": "OpenAI Releases GPT-4", "url": "https://news.openai.com/gpt4", "source": "openai.com", "timestamp": 1001},
        {"title": "OpenAI launches GPT-4 model", "url": "https://openai.com/blog", "source": "openai.com", "timestamp": 1002},
        {"title": "Google announces Gemini", "url": "https://google.com/gemini", "source": "google.com", "timestamp": 1003},
        {"title": "New AI model from OpenAI", "url": "https://reddit.com/r/...", "source": "reddit.com", "timestamp": 1004},
    ]

    print(f"Input: {len(test_items)} items")
    result = deduplicator.deduplicate(test_items)
    print(f"Output: {len(result)} items")
    for item in result:
        print(f"  - {item['title']}")
