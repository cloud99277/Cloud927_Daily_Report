"""Topic clustering for organizing articles by theme."""

import logging
import re
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)


class Clusterer:
    """
    Topic clustering for organizing articles by theme.
    Uses keyword-based classification and LLM-like heuristics.
    """

    # Topic keywords for classification
    TOPIC_KEYWORDS = {
        "AI模型更新": [
            "gpt", "llm", "model", "训练", "模型", "参数", "能力", "发布", "更新",
            "openai", "anthropic", "gemini", "claude", "llama", "mistral"
        ],
        "开源工具/框架": [
            "github", "开源", "framework", "库", "工具", "库", "repository",
            "release", "library", "toolkit", "sdk", "api"
        ],
        "研究论文/突破": [
            "paper", "论文", "research", "研究", "arxiv", "学术", "突破",
            "benchmark", "experiment", "performance", "sota"
        ],
        "产品发布/融资": [
            "product", "产品", "launch", "发布", "funding", "融资", "investment",
            "series", "ipo", "acquisition", "收购", "startup"
        ],
        "行业动态/政策": [
            "policy", "政策", "regulation", "监管", "regulation", "industry",
            "行业", "market", "市场", "趋势", "trend"
        ],
        "全球要闻": [
            "war", "战争", "election", "选举", "president", "主席", "government",
            "政府", "international", "国际", "外交", "制裁"
        ],
        "中国社会": [
            "中国", "国内", "北京", "上海", "深圳", "政府", "企业",
            "两会", "十四五", "改革开放"
        ],
        "AI应用场景": [
            "application", "应用", "use case", "案例", "医疗", "教育", "金融",
            "自动驾驶", "智能", "ai", "assistant"
        ]
    }

    def __init__(self, max_cluster_size: int = 5):
        """
        Initialize the clusterer.

        Args:
            max_cluster_size: Maximum number of items per cluster
        """
        self.max_cluster_size = max_cluster_size

    def _extract_keywords(self, text: str) -> set[str]:
        """Extract keywords from text."""
        if not text:
            return set()

        # Convert to lowercase and extract words
        text = text.lower()
        words = re.findall(r"\b[a-z]+\b", text)

        # Also extract Chinese characters
        chinese = re.findall(r"[\u4e00-\u9fa5]+", text)

        return set(words) | set(chinese)

    def _classify_item(self, item: dict) -> str:
        """Classify an item into a topic category."""
        title = item.get("title", "")
        content = item.get("content", "") or item.get("description", "") or ""

        text = f"{title} {content}"
        text_lower = text.lower()
        keywords = self._extract_keywords(text)

        scores = {}

        for category, category_keywords in self.TOPIC_KEYWORDS.items():
            score = 0
            for keyword in category_keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in text_lower:
                    # Check if keyword appears multiple times
                    count = text_lower.count(keyword_lower)
                    score += count

                if keyword_lower in keywords:
                    score += 2  # Higher weight for extracted keywords

            scores[category] = score

        # Return category with highest score, default to first if no match
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return "其他"

    def _calculate_importance(self, item: dict) -> float:
        """Calculate importance score for an item."""
        score = 0

        # Source priority
        url = item.get("url", "")
        source = item.get("source", "")

        priority_domains = {
            "arxiv.org": 10,
            "openai.com": 10,
            "anthropic.com": 10,
            "google.com": 9,
            "meta.com": 9,
            "reuters.com": 8,
            "apnews.com": 8,
            "bbc.com": 7,
            "github.com": 6,
            "huggingface.co": 6,
        }

        for domain, s in priority_domains.items():
            if domain in (url.lower() if url else ""):
                score += s
                break

        # Engagement metrics
        score += min(item.get("score", 0) / 10, 5)  # Up to 5 points
        score += min(item.get("replies", 0) / 5, 3)  # Up to 3 points
        score += min(item.get("views", 0) / 100, 2)  # Up to 2 points

        # Recency bonus
        timestamp = item.get("timestamp", 0) or item.get("time", 0)
        import time as time_module
        if isinstance(timestamp, (int, float)):
            hours_old = (time_module.time() - timestamp) / 3600
            if hours_old < 1:
                score += 3
            elif hours_old < 6:
                score += 2
            elif hours_old < 12:
                score += 1

        return score

    def cluster(
        self,
        items: list[dict],
        categories: list[str] | None = None
    ) -> dict[str, list[dict]]:
        """
        Cluster items by topic.

        Args:
            items: List of items to cluster
            categories: List of categories to use (default: all defined)

        Returns:
            Dict mapping category names to lists of items
        """
        if not items:
            logger.warning("No items to cluster")
            return {}

        logger.info(f"Clustering {len(items)} items")

        if categories is None:
            categories = list(self.TOPIC_KEYWORDS.keys()) + ["其他"]

        # Initialize clusters
        clusters = defaultdict(list)

        # Classify and add to clusters
        for item in items:
            category = self._classify_item(item)
            item["_importance_score"] = self._calculate_importance(item)
            clusters[category].append(item)

        # Sort each cluster by importance
        for category in clusters:
            clusters[category] = sorted(
                clusters[category],
                key=lambda x: x.get("_importance_score", 0),
                reverse=True
            )
            # Limit cluster size
            if len(clusters[category]) > self.max_cluster_size:
                clusters[category] = clusters[category][:self.max_cluster_size]

        # Log cluster sizes
        for category, items_list in clusters.items():
            logger.info(f"  {category}: {len(items_list)} items")

        # Remove empty clusters and convert to regular dict
        return {k: v for k, v in clusters.items() if v}

    def cluster_with_subcategories(
        self,
        items: list[dict]
    ) -> dict[str, dict[str, list[dict]]]:
        """
        Cluster items with subcategories for finer-grained organization.

        Args:
            items: List of items to cluster

        Returns:
            Dict mapping category to subcategory to items
        """
        main_clusters = self.cluster(items)

        result = {}
        for category, category_items in main_clusters.items():
            sub_clusters = self._subclassify(category_items, category)
            result[category] = sub_clusters

        return result

    def _subclassify(
        self,
        items: list[dict],
        parent_category: str
    ) -> dict[str, list[dict]]:
        """Create subcategories within a main category."""
        subcategories = defaultdict(list)

        for item in items:
            title = item.get("title", "").lower()

            # AI subcategories
            if parent_category == "AI模型更新":
                if "gpt" in title or "openai" in title:
                    subcategories["OpenAI/GPT系列"] = []
                elif "claude" in title or "anthropic" in title:
                    subcategories["Anthropic/Claude系列"] = []
                elif "gemini" in title or "google" in title:
                    subcategories["Google/Gemini系列"] = []
                elif "llama" in title or "meta" in title:
                    subcategories["Meta/LLaMA系列"] = []
                else:
                    subcategories["其他模型"] = []

            elif parent_category == "开源工具/框架":
                if "github" in title or "repository" in title:
                    subcategories["GitHub项目"] = []
                elif "library" in title or "framework" in title:
                    subcategories["框架/库"] = []
                elif "sdk" in title or "api" in title:
                    subcategories["SDK/API"] = []
                else:
                    subcategories["其他工具"] = []

            elif parent_category == "研究论文/突破":
                if "arxiv" in title:
                    subcategories["arXiv论文"] = []
                elif "benchmark" in title or "sota" in title:
                    subcategories["基准测试"] = []
                else:
                    subcategories["研究进展"] = []

            elif parent_category == "产品发布/融资":
                if "funding" in title or "investment" in title or "融资" in title:
                    subcategories["融资/投资"] = []
                elif "launch" in title or "发布" in title or "release" in title:
                    subcategories["产品发布"] = []
                elif "acquisition" in title or "收购" in title:
                    subcategories["收购/并购"] = []
                else:
                    subcategories["行业动态"] = []

            else:
                subcategories["最新动态"] = []

            # Add item to appropriate subcategory
            for subcat in subcategories:
                if not subcategories[subcat]:
                    subcategories[subcat].append(item)
                    break

        # Clean up empty subcategories
        return {k: v for k, v in subcategories.items() if v}

    def get_cluster_summary(self, clusters: dict[str, list[dict]]) -> str:
        """Generate a summary of the clusters."""
        summary_parts = []

        for category, items in sorted(
            clusters.items(),
            key=lambda x: len(x[1]),
            reverse=True
        ):
            top_item = items[0] if items else {}
            summary_parts.append(
                f"- **{category}**: {len(items)} items"
                + (f" (Top: {top_item.get('title', '')[:40]}...)" if top_item else "")
            )

        return "\n".join(summary_parts)


if __name__ == "__main__":
    # Test clustering
    clusterer = Clusterer()

    test_items = [
        {"title": "OpenAI releases GPT-5 with improved reasoning", "url": "https://openai.com/gpt5", "score": 500, "source": "openai.com"},
        {"title": "Meta releases LLaMA 3 weights", "url": "https://github.com/meta/llama", "score": 300, "source": "github.com"},
        {"title": "New paper on transformer efficiency", "url": "https://arxiv.org/abs/1234", "source": "arxiv.org", "replies": 50},
        {"title": "Google announces Gemini Ultra", "url": "https://google.com/gemini", "score": 400, "source": "google.com"},
        {"title": "AI startup raises $100M Series B", "url": "https://techcrunch.com/funding", "source": "techcrunch.com", "views": 5000},
        {"title": "China's new AI regulations", "url": "https://thepaper.cn/ai-policy", "source": "thepaper.cn"},
        {"title": "New Python ML library released", "url": "https://github.com/user/ml-tool", "score": 100, "source": "github.com"},
    ]

    print("Input items:", len(test_items))
    clusters = clusterer.cluster(test_items)
    print("\nClusters:")
    for category, items in clusters.items():
        print(f"\n{category} ({len(items)} items):")
        for item in items:
            print(f"  - {item['title'][:50]}")
