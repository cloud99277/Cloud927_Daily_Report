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
        Deduplicate a list of items, tracking cross-source counts.

        When duplicates are found, the kept item receives:
        - cross_source_count: number of sources that reported the same event
        - reported_by: list of source names that reported it

        Args:
            items: List of items with 'title' and 'url' fields
            group_by_source: If True, only deduplicate within same source

        Returns:
            Deduplicated list of items with cross-source metadata
        """
        if not items:
            return []

        logger.info(f"Deduplicating {len(items)} items")

        # Sort by priority first (higher priority sources first)
        sorted_items = sorted(
            items,
            key=lambda x: (self._get_source_priority(x), x.get("timestamp", 0)),
            reverse=True
        )

        # Map from kept-item title -> index in results list
        seen_fingerprints = set()
        seen_titles: dict[str, int] = {}  # title -> index in results
        results: list[dict] = []

        for item in sorted_items:
            title = item.get("title", "")
            source = item.get("source", "unknown")

            fingerprint = self._create_fingerprint(item)
            if fingerprint in seen_fingerprints:
                # Exact fingerprint match - merge source info into existing
                self._merge_source_into(results, seen_titles, title, source)
                continue

            # Check for similar titles
            matched_title = self._find_matching_title(
                title, source, item, seen_titles, results, group_by_source
            )

            if matched_title is not None:
                # Duplicate found - merge source info
                self._merge_source_into(results, seen_titles, matched_title, source)
                continue

            # New unique item - initialize cross-source metadata
            item["cross_source_count"] = 1
            item["reported_by"] = [source]
            seen_fingerprints.add(fingerprint)
            seen_titles[title] = len(results)
            results.append(item)

        logger.info(f"Deduplication complete: {len(items)} -> {len(results)} items")
        return results

    def _find_matching_title(
        self,
        title: str,
        source: str,
        item: dict,
        seen_titles: dict[str, int],
        results: list[dict],
        group_by_source: bool,
    ) -> str | None:
        """Find a matching title in seen_titles. Returns the matched title or None."""
        for seen_title, idx in list(seen_titles.items()):
            similarity = self._calculate_similarity(title, seen_title)

            if similarity >= self.exact_match_threshold:
                return seen_title
            elif similarity >= self.fuzzy_match_threshold:
                seen_source = results[idx].get("source", "unknown")
                if group_by_source and source == seen_source:
                    return seen_title
                elif self._get_source_priority(item) > self.source_priority.get(seen_source, 50):
                    # Higher priority: replace the kept item but preserve its metadata
                    old = results[idx]
                    item["cross_source_count"] = old.get("cross_source_count", 1)
                    item["reported_by"] = list(old.get("reported_by", [seen_source]))
                    results[idx] = item
                    seen_titles[title] = idx
                    del seen_titles[seen_title]
                    return title  # will merge current source into the replaced item
                else:
                    return seen_title
        return None

    @staticmethod
    def _merge_source_into(
        results: list[dict],
        seen_titles: dict[str, int],
        matched_title: str,
        source: str,
    ) -> None:
        """Merge a duplicate source into the kept item's metadata."""
        idx = seen_titles.get(matched_title)
        if idx is None:
            return
        kept = results[idx]
        reported = kept.get("reported_by", [])
        if source not in reported:
            reported.append(source)
            kept["reported_by"] = reported
            kept["cross_source_count"] = len(reported)

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

        This is a convenience wrapper around deduplicate() which already
        tracks cross_source_count and reported_by. The returned items
        have those fields populated.

        Args:
            items: List of potentially duplicate items

        Returns:
            List with merged duplicates, each carrying cross_source_count
            and reported_by metadata.
        """
        return self.deduplicate(items)


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
