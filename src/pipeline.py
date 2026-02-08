"""Pipeline orchestrator for Cloud927 Daily Report."""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any

from src.config import Config
from src.models import NewsItem
from src.utils.logger import setup_logger

logger = setup_logger("pipeline")


class Pipeline:
    """Orchestrates the full Cloud927 report generation pipeline."""

    def __init__(self, obsidian_vault_path: str = ""):
        self.config = Config()
        self.obsidian_vault_path = obsidian_vault_path

    def run(self) -> str:
        """Execute the full pipeline and return the report."""
        logger.info("Starting Cloud927 pipeline")

        items = self.fetch()
        items = self.deduplicate(items)
        clusters = self.cluster(items)
        timeline = self.track(items)
        report = self.generate(items, clusters, timeline)
        self.save(report)

        logger.info("Pipeline complete")
        return report

    def fetch(self) -> list[NewsItem]:
        """Parallel fetch from all enabled sources."""
        fetchers = self._build_fetcher_registry()
        max_workers = self.config._config.get("pipeline", {}).get("max_workers", 12)
        all_items: list[NewsItem] = []

        logger.info(f"Fetching from {len(fetchers)} sources (max_workers={max_workers})")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_name = {
                executor.submit(f.fetch): name for name, f in fetchers.items()
            }
            for future in as_completed(future_to_name):
                name = future_to_name[future]
                try:
                    items = future.result()
                    all_items.extend(items)
                    logger.info(f"  {name}: {len(items)} items")
                except Exception as e:
                    logger.error(f"  {name} failed: {e}")

        logger.info(f"Total fetched: {len(all_items)} items")
        return all_items

    def deduplicate(self, items: list[NewsItem]) -> list[NewsItem]:
        """Cross-source deduplication with metadata merging."""
        from src.processor.deduplicator import Deduplicator

        dedup_cfg = self.config.processing.get("deduplication", {})
        if not dedup_cfg.get("enabled", True):
            return items

        deduplicator = Deduplicator(
            exact_match_threshold=dedup_cfg.get("exact_match_threshold", 0.95),
            fuzzy_match_threshold=dedup_cfg.get("fuzzy_match_threshold", 0.80),
        )

        dicts = [item.to_dict() for item in items]
        deduped = deduplicator.deduplicate(dicts)
        return [NewsItem.from_dict(d) for d in deduped]

    def cluster(self, items: list[NewsItem]) -> dict[str, list[dict]]:
        """Cluster items by topic."""
        from src.processor.clustering import Clusterer

        cluster_cfg = self.config.processing.get("clustering", {})
        if not cluster_cfg.get("enabled", True):
            return {}

        clusterer = Clusterer(max_cluster_size=cluster_cfg.get("max_cluster_size", 5))
        dicts = [item.to_dict() for item in items]
        return clusterer.cluster(dicts)

    def track(self, items: list[NewsItem]) -> dict[str, Any]:
        """Track entity timeline."""
        from src.processor.timeline_tracker import TimelineTracker

        timeline_cfg = self.config.processing.get("timeline", {})
        if not timeline_cfg.get("enabled", True):
            return {"new": [], "updated": [], "ongoing": [], "entities_found": []}

        tracker = TimelineTracker(
            state_file=timeline_cfg.get("state_file", "data/timeline_state.json"),
            entities=timeline_cfg.get("entities"),
        )
        dicts = [item.to_dict() for item in items]
        return tracker.track(dicts)

    def generate(
        self,
        items: list[NewsItem],
        clusters: dict[str, list[dict]],
        timeline: dict[str, Any],
    ) -> str:
        """Generate report using dual-layer LLM (preprocess + insight)."""
        from src.generator_v3 import ReportGenerator

        item_dicts = [item.to_dict() for item in items]
        generator = ReportGenerator(config=self.config)
        return generator.generate_report(item_dicts, clusters, timeline)

    def save(self, report: str) -> None:
        """Save report to Obsidian vault."""
        if not self.obsidian_vault_path:
            logger.warning("No Obsidian vault path configured, skipping save")
            return

        from src.storage import ObsidianWriter
        writer = ObsidianWriter(vault_path=self.obsidian_vault_path)
        filepath = writer.write_report(report)
        logger.info(f"Report saved: {filepath}")

    def _build_fetcher_registry(self) -> dict:
        """Build registry of all enabled fetchers from config."""
        registry = {}
        self._register_existing_fetchers(registry)
        self._register_new_fetchers(registry)
        return registry

    def _register_existing_fetchers(self, registry: dict) -> None:
        """Register existing v3 fetchers."""
        from src.fetchers.hn_fetcher import HNFetcher
        from src.fetchers.hn_show_fetcher import HNShowFetcher
        from src.fetchers.github_fetcher import GitHubFetcher
        from src.fetchers.hf_api_fetcher import HuggingFaceAPIFetcher
        from src.fetchers.ai_news_fetcher import AINewsFetcher
        from src.fetchers.ph_fetcher import ProductHuntFetcher
        from src.fetchers.reddit_fetcher import RedditAIFetcher
        from src.fetchers.v2ex_fetcher import V2EXFetcher
        from src.fetchers.twitter_fetcher import TwitterFetcher
        from src.fetchers.arxiv_fetcher import ArxivFetcher
        from src.fetchers.news.reuters_fetcher import ReutersFetcher
        from src.fetchers.news.ap_news_fetcher import APNewsFetcher
        from src.fetchers.news.bbc_fetcher import BBCWorldFetcher
        from src.fetchers.china.jinri_remai_fetcher import JinriRemaiFetcher
        from src.fetchers.china.sina_fetcher import SinaFetcher
        from src.fetchers.china.ifeng_fetcher import IfengFetcher
        from src.fetchers.china.pengpai_fetcher import PengpaiFetcher
        from src.fetchers.china.caixin_fetcher import CaixinFetcher

        existing = {
            "hn": HNFetcher(),
            "hn_show": HNShowFetcher(),
            "github": GitHubFetcher(),
            "hf": HuggingFaceAPIFetcher(),
            "ai_news": AINewsFetcher(),
            "ph": ProductHuntFetcher(),
            "reddit": RedditAIFetcher(),
            "v2ex": V2EXFetcher(),
            "twitter": TwitterFetcher(),
            "arxiv": ArxivFetcher(),
            "reuters": ReutersFetcher(),
            "ap_news": APNewsFetcher(),
            "bbc": BBCWorldFetcher(),
            "jinri_remai": JinriRemaiFetcher(),
            "sina": SinaFetcher(),
            "ifeng": IfengFetcher(),
            "pengpai": PengpaiFetcher(),
            "caixin": CaixinFetcher(),
        }

        for name, fetcher in existing.items():
            if self.config.is_source_enabled(name):
                registry[name] = fetcher

    def _register_new_fetchers(self, registry: dict) -> None:
        """Register new sector fetchers (safe import with fallback)."""
        new_fetchers = {
            "techcrunch": "src.fetchers.startup.techcrunch_fetcher.TechCrunchFetcher",
            "36kr_startup": "src.fetchers.startup.kr36_fetcher.Kr36Fetcher",
            "itjuzi": "src.fetchers.startup.itjuzi_fetcher.ITJuziFetcher",
            "ft": "src.fetchers.finance.ft_fetcher.FTFetcher",
            "bloomberg": "src.fetchers.finance.bloomberg_fetcher.BloombergFetcher",
            "yahoo_finance": "src.fetchers.finance.yahoo_finance_fetcher.YahooFinanceFetcher",
            "coindesk": "src.fetchers.crypto.coindesk_fetcher.CoinDeskFetcher",
            "theblock": "src.fetchers.crypto.theblock_fetcher.TheBlockFetcher",
            "decrypt": "src.fetchers.crypto.decrypt_fetcher.DecryptFetcher",
            "techpolicy": "src.fetchers.policy.techpolicy_fetcher.TechPolicyFetcher",
            "china_policy": "src.fetchers.policy.china_policy_fetcher.ChinaPolicyFetcher",
        }

        for name, class_path in new_fetchers.items():
            if not self.config.is_source_enabled(name):
                continue
            try:
                module_path, class_name = class_path.rsplit(".", 1)
                import importlib
                module = importlib.import_module(module_path)
                cls = getattr(module, class_name)
                registry[name] = cls()
            except (ImportError, AttributeError) as e:
                logger.debug(f"Skipping {name}: {e}")
