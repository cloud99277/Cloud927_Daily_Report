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

    # Topic keywords for classification (6 sectors)
    TOPIC_KEYWORDS = {
        "AI前沿": [
            "gpt", "llm", "model", "claude", "gemini", "llama", "mistral",
            "openai", "anthropic", "transformer", "训练", "模型", "参数",
            "ai", "机器学习", "深度学习", "neural", "benchmark", "arxiv",
            "论文", "research", "开源", "github", "framework", "huggingface",
        ],
        "创业/投融资": [
            "funding", "融资", "startup", "series", "ipo", "acquisition",
            "收购", "techcrunch", "36kr", "投资", "估值", "valuation",
            "venture", "capital", "angel", "seed", "unicorn", "独角兽",
        ],
        "金融/宏观": [
            "stock", "market", "fed", "央行", "gdp", "inflation", "利率",
            "bloomberg", "finance", "经济", "货币", "债券", "bond",
            "treasury", "recession", "衰退", "cpi", "就业", "unemployment",
        ],
        "Web3/Crypto": [
            "bitcoin", "ethereum", "crypto", "blockchain", "defi", "nft",
            "web3", "coindesk", "token", "mining", "挖矿", "交易所",
            "wallet", "钱包", "solana", "layer2", "dao",
        ],
        "科技政策": [
            "policy", "regulation", "监管", "政策", "法规", "antitrust",
            "privacy", "数据安全", "合规", "compliance", "审查", "立法",
            "legislation", "ban", "禁令", "制裁", "sanction",
        ],
        "全球重大事件": [
            "war", "election", "选举", "government", "政府", "international",
            "制裁", "reuters", "外交", "军事", "冲突", "conflict",
            "summit", "峰会", "联合国", "nato", "地震", "灾害",
        ],
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
                # Use word boundary for English keywords, plain `in` for Chinese
                is_ascii = keyword_lower.isascii()
                if is_ascii:
                    match = re.search(r'\b' + re.escape(keyword_lower) + r'\b', text_lower)
                    if match:
                        count = len(re.findall(r'\b' + re.escape(keyword_lower) + r'\b', text_lower))
                        score += count
                else:
                    if keyword_lower in text_lower:
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
            subcat = self._pick_subcategory(title, parent_category)
            subcategories[subcat].append(item)

        return dict(subcategories)

    def _pick_subcategory(self, title: str, parent_category: str) -> str:
        """Determine the subcategory name for an item based on its title."""
        if parent_category == "AI前沿":
            if "gpt" in title or "openai" in title:
                return "OpenAI/GPT系列"
            if "claude" in title or "anthropic" in title:
                return "Anthropic/Claude系列"
            if "gemini" in title or "google" in title:
                return "Google/Gemini系列"
            if "llama" in title or "meta" in title:
                return "Meta/LLaMA系列"
            if "arxiv" in title or "paper" in title or "论文" in title:
                return "研究论文"
            if "github" in title or "开源" in title:
                return "开源项目"
            return "其他"

        if parent_category == "创业/投融资":
            if "funding" in title or "融资" in title or "investment" in title:
                return "融资/投资"
            if "ipo" in title:
                return "IPO"
            if "acquisition" in title or "收购" in title:
                return "收购/并购"
            return "创业动态"

        if parent_category == "金融/宏观":
            if "fed" in title or "央行" in title or "利率" in title:
                return "央行/货币政策"
            if "stock" in title or "market" in title or "股" in title:
                return "市场行情"
            return "宏观经济"

        if parent_category == "Web3/Crypto":
            if "bitcoin" in title or "btc" in title:
                return "Bitcoin"
            if "ethereum" in title or "eth" in title:
                return "Ethereum"
            if "defi" in title:
                return "DeFi"
            return "行业动态"

        if parent_category == "科技政策":
            if "antitrust" in title or "反垄断" in title:
                return "反垄断"
            if "privacy" in title or "数据安全" in title:
                return "数据隐私"
            return "政策法规"

        if parent_category == "全球重大事件":
            if "war" in title or "军事" in title or "冲突" in title:
                return "军事/冲突"
            if "election" in title or "选举" in title:
                return "选举/政治"
            return "国际要闻"

        return "最新动态"

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
