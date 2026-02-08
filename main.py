"""Main entry point for the Daily Report Generator v3.0."""

import os
import sys
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from src.utils.logger import setup_logger
from src.config import config

# v2.0 Fetchers
from src.fetchers.hn_fetcher import HNFetcher
from src.fetchers.hn_show_fetcher import HNShowFetcher
from src.fetchers.github_fetcher import GitHubFetcher
from src.fetchers.hf_api_fetcher import HuggingFaceAPIFetcher
from src.fetchers.ai_news_fetcher import AINewsFetcher
from src.fetchers.ph_fetcher import ProductHuntFetcher
from src.fetchers.reddit_fetcher import RedditAIFetcher
from src.fetchers.v2ex_fetcher import V2EXFetcher

# v3.0 News Fetchers
from src.fetchers.news.reuters_fetcher import ReutersFetcher
from src.fetchers.news.ap_news_fetcher import APNewsFetcher
from src.fetchers.news.bbc_fetcher import BBCWorldFetcher

# v3.0 China Fetchers
from src.fetchers.china.jinri_remai_fetcher import JinriRemaiFetcher
from src.fetchers.china.sina_fetcher import SinaFetcher
from src.fetchers.china.ifeng_fetcher import IfengFetcher
from src.fetchers.china.pengpai_fetcher import PengpaiFetcher
from src.fetchers.china.caixin_fetcher import CaixinFetcher

# v3.0 Supplementary Fetchers
from src.fetchers.twitter_fetcher import TwitterFetcher
from src.fetchers.arxiv_fetcher import ArxivFetcher

# v3.0 Processors
from src.processor.temporal_filter import TemporalFilter
from src.processor.deduplicator import Deduplicator
from src.processor.clustering import Clusterer
from src.processor.timeline_tracker import TimelineTracker
from src.storage.raw_data_manager import RawDataManager

from src.generator import LLMClient
from src.storage import ObsidianWriter


def load_environment() -> bool:
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        return True
    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists():
        load_dotenv(cwd_env)
        return True
    return False


def validate_obsidian_path(path: str) -> bool:
    """Validate that the Obsidian vault path exists."""
    return Path(path).exists() and Path(path).is_dir()


# v2.0 Data Fetchers
def fetch_hn_data() -> dict[str, Any]:
    """Fetch Hacker News data."""
    fetcher = HNFetcher()
    return fetcher.fetch()


def fetch_github_data() -> dict[str, Any]:
    """Fetch GitHub trending data with README."""
    fetcher = GitHubFetcher()
    trending = fetcher.fetch_trending(language="python", limit=5, fetch_readme=True)
    ai_trending = fetcher.fetch_ai_trending(limit=5, fetch_readme=True)
    return {"trending": trending, "ai_trending": ai_trending}


def fetch_hf_data() -> list[dict[str, Any]]:
    """Fetch HuggingFace papers via API."""
    fetcher = HuggingFaceAPIFetcher()
    return fetcher.fetch()


def fetch_ai_news_data() -> list[dict[str, Any]]:
    """Fetch AI news from OpenAI, Anthropic, Google, Meta."""
    fetcher = AINewsFetcher()
    return fetcher.fetch()


def fetch_ph_data() -> list[dict[str, Any]]:
    """Fetch AI products from Product Hunt."""
    fetcher = ProductHuntFetcher()
    return fetcher.fetch().get("products", [])


def fetch_reddit_data() -> list[dict[str, Any]]:
    """Fetch top AI discussions from Reddit."""
    fetcher = RedditAIFetcher()
    return fetcher.fetch()


def fetch_v2ex_data() -> list[dict[str, Any]]:
    """Fetch V2EX discussions."""
    fetcher = V2EXFetcher()
    return fetcher.fetch()


def fetch_hn_show_data() -> dict[str, Any]:
    """Fetch HN Show HN posts."""
    fetcher = HNShowFetcher()
    return fetcher.fetch()


# v3.0 News Fetchers
def fetch_reuters_data() -> list[dict[str, Any]]:
    """Fetch Reuters world news."""
    fetcher = ReutersFetcher()
    return fetcher.fetch(limit=10)


def fetch_ap_news_data() -> list[dict[str, Any]]:
    """Fetch AP News stories."""
    fetcher = APNewsFetcher()
    return fetcher.fetch(limit=10)


def fetch_bbc_data() -> list[dict[str, Any]]:
    """Fetch BBC World News."""
    fetcher = BBCWorldFetcher()
    return fetcher.fetch(limit=10)


# v3.0 China Fetchers
def fetch_jinri_remai_data() -> list[dict[str, Any]]:
    """Fetch AI news from Jinri Toutiao."""
    fetcher = JinriRemaiFetcher()
    return fetcher.fetch(limit=10)


def fetch_sina_data() -> list[dict[str, Any]]:
    """Fetch news from Sina."""
    fetcher = SinaFetcher()
    return fetcher.fetch(limit=10)


def fetch_ifeng_data() -> list[dict[str, Any]]:
    """Fetch news from Ifeng."""
    fetcher = IfengFetcher()
    return fetcher.fetch(limit=10)


def fetch_pengpai_data() -> list[dict[str, Any]]:
    """Fetch news from 澎湃新闻."""
    fetcher = PengpaiFetcher()
    return fetcher.fetch(limit=10)


def fetch_caixin_data() -> list[dict[str, Any]]:
    """Fetch news from 财新."""
    fetcher = CaixinFetcher()
    return fetcher.fetch(limit=10)


# v3.0 Supplementary Fetchers
def fetch_twitter_data() -> list[dict[str, Any]]:
    """Fetch AI tweets from Twitter/X."""
    fetcher = TwitterFetcher()
    return fetcher.fetch(limit_per_user=5)


def fetch_arxiv_data() -> list[dict[str, Any]]:
    """Fetch AI papers from ArXiv."""
    fetcher = ArxivFetcher()
    return fetcher.fetch(max_results=20, days_back=14)


# v2.0 Parallel Fetch
def fetch_all_v2_data_parallel() -> dict[str, Any]:
    """Fetch all v2.0 data sources in parallel."""
    logger = setup_logger("fetcher")
    logger.info("Starting v2.0 parallel data fetch")

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            "hn": executor.submit(fetch_hn_data),
            "gh": executor.submit(fetch_github_data),
            "hf": executor.submit(fetch_hf_data),
            "ai_news": executor.submit(fetch_ai_news_data),
            "ph": executor.submit(fetch_ph_data),
            "reddit": executor.submit(fetch_reddit_data),
            "v2ex": executor.submit(fetch_v2ex_data),
            "hn_show": executor.submit(fetch_hn_show_data),
        }

        results = {}
        for future in as_completed(futures.values()):
            for key, f in futures.items():
                if f is future or f == future:
                    try:
                        results[key] = future.result()
                        count = len(results.get(key, [])) if isinstance(results.get(key), list) else 'dict'
                        logger.info(f"{key.upper()} fetched: {count}")
                    except Exception as e:
                        logger.error(f"{key.upper()} failed: {e}")
                        results[key] = []
                    break

    return results


# v3.0 Full Fetch
def fetch_all_v3_data_parallel() -> dict[str, Any]:
    """Fetch all v3.0 data sources in parallel."""
    logger = setup_logger("fetcher")
    logger.info("Starting v3.0 full parallel data fetch")

    # Initialize processors
    temporal_filter = TemporalFilter()
    deduplicator = Deduplicator()
    clusterer = Clusterer()
    timeline_tracker = TimelineTracker()
    raw_data_manager = RawDataManager()

    # v3.0 has 8 original + 3 news + 5 china + 2 supplementary = 18 sources
    fetchers = {
        # v2.0 Original
        "hn": fetch_hn_data,
        "gh": fetch_github_data,
        "hf": fetch_hf_data,
        "ai_news": fetch_ai_news_data,
        "ph": fetch_ph_data,
        "reddit": fetch_reddit_data,
        "v2ex": fetch_v2ex_data,
        "hn_show": fetch_hn_show_data,
        # v3.0 News
        "reuters": fetch_reuters_data,
        "ap_news": fetch_ap_news_data,
        "bbc": fetch_bbc_data,
        # v3.0 China
        "jinri_remai": fetch_jinri_remai_data,
        "sina": fetch_sina_data,
        "ifeng": fetch_ifeng_data,
        "pengpai": fetch_pengpai_data,
        "caixin": fetch_caixin_data,
        # v3.0 Supplementary
        "twitter": fetch_twitter_data,
        "arxiv": fetch_arxiv_data,
    }

    results = {}

    with ThreadPoolExecutor(max_workers=12) as executor:
        future_to_key = {executor.submit(fn): key for key, fn in fetchers.items()}

        for future in as_completed(future_to_key):
            key = future_to_key[future]
            try:
                data = future.result()
                results[key] = data

                # Apply temporal filtering
                source_type = _get_source_type(key)
                if source_type:
                    data = temporal_filter.filter_by_time(data, source_type)

                # Save raw data for incremental fetching
                raw_data_manager.save_raw(key, data)

                count = len(data) if isinstance(data, (list, dict)) else 0
                logger.info(f"{key.upper()} fetched: {count} items")
            except Exception as e:
                logger.error(f"{key.upper()} failed: {e}")
                results[key] = []

    # Cross-source deduplication
    all_items = []
    for key, source_data in results.items():
        if isinstance(source_data, list):
            for item in source_data:
                item["_source"] = key
                all_items.append(item)
        elif isinstance(source_data, dict):
            for item_list in source_data.values():
                if isinstance(item_list, list):
                    for item in item_list:
                        item["_source"] = key
                        all_items.append(item)

    deduplicated = deduplicator.deduplicate(all_items)

    # Clustering
    clusters = clusterer.cluster(deduplicated)

    # Timeline tracking
    timeline = timeline_tracker.track(deduplicated)

    return {
        "raw_results": results,
        "deduplicated": deduplicated,
        "clusters": clusters,
        "timeline": timeline,
    }


def _get_source_type(source: str) -> str:
    """Map source to source type for temporal filtering."""
    source_types = {
        "hn": "social",
        "github": "github",
        "hf": "paper",
        "ai_news": "news",
        "ph": "social",
        "reddit": "social",
        "v2ex": "social",
        "hn_show": "social",
        "reuters": "news",
        "ap_news": "news",
        "bbc": "news",
        "jinri_remai": "news",
        "sina": "news",
        "ifeng": "news",
        "pengpai": "news",
        "caixin": "news",
        "twitter": "social",
        "arxiv": "paper",
    }
    return source_types.get(source, "default")


def generate_v2_report(
    results: dict[str, Any],
    api_key: str
) -> str:
    """Generate v2.0 style report."""
    logger = setup_logger("generator")
    logger.info("Generating v2.0 report")

    client = LLMClient(api_key=api_key)

    hn_data = results.get("hn", {}).get("stories", [])
    gh_data = results.get("gh", {}).get("trending", []) + results.get("gh", {}).get("ai_trending", [])
    showhn_posts = results.get("hn_show", {}).get("posts", [])
    v2ex_data = results.get("v2ex", [])
    ai_news_data = results.get("ai_news", [])
    ph_data = results.get("ph", [])
    reddit_data = results.get("reddit", [])
    hf_data = results.get("hf", [])

    return client.generate_report(
        hn_data=hn_data,
        gh_data=gh_data,
        hf_data=hf_data,
        showhn_data=showhn_posts,
        v2ex_data=v2ex_data,
        ai_news_data=ai_news_data,
        ph_data=ph_data,
        reddit_data=reddit_data,
    )


def generate_v3_report(
    results: dict[str, Any],
    api_key: str
) -> str:
    """Generate v3.0 enhanced report."""
    logger = setup_logger("generator")
    logger.info("Generating v3.0 report")

    # Import v3 generator (to be created)
    from src.generator_v3 import LLMClientV3

    client = LLMClientV3(api_key=api_key)

    return client.generate_report(
        raw_results=results["raw_results"],
        clusters=results["clusters"],
        timeline=results["timeline"],
    )


def save_report(content: str, vault_path: str) -> Path:
    """Save report to Obsidian vault."""
    writer = ObsidianWriter(vault_path=vault_path)
    return writer.write_report(content)


def main(mode: str = "v2") -> int:
    """Main entry point.

    Args:
        mode: "v2" for original 8 sources, "v3" for full 18 sources
    """
    logger = setup_logger("daily_report")
    logger.info(f"Starting Cloud927 v{mode} Daily Report Generator")

    try:
        logger.info("Loading environment variables")
        if not load_environment():
            logger.warning(".env not found")

        obsidian_path = os.environ.get("OBSIDIAN_VAULT_PATH", "")
        api_key = os.environ.get("GEMINI_API_KEY", "")

        if not obsidian_path:
            logger.error("OBSIDIAN_VAULT_PATH not set")
            return 1
        if not validate_obsidian_path(obsidian_path):
            logger.error(f"OBSIDIAN_VAULT_PATH invalid: {obsidian_path}")
            return 1
        if not api_key:
            logger.error("GEMINI_API_KEY not set")
            return 1

        logger.info(f"Vault: {obsidian_path}")

        if mode == "v2":
            # v2.0 Mode
            logger.info("Fetching from 8 v2.0 data sources...")
            results = fetch_all_v2_data_parallel()

            logger.info(f"HN: {len(results.get('hn', {}).get('stories', []))} stories")
            logger.info(f"GitHub: {len(results.get('gh', {}).get('trending', []))} trending")
            logger.info(f"HuggingFace: {len(results.get('hf', []))} papers")
            logger.info(f"AI News: {len(results.get('ai_news', []))} articles")
            logger.info(f"Product Hunt: {len(results.get('ph', []))} products")
            logger.info(f"Reddit: {len(results.get('reddit', []))} discussions")
            logger.info(f"V2EX: {len(results.get('v2ex', []))} posts")

            logger.info("Generating v2.0 report...")
            report = generate_v2_report(results, api_key)

        else:
            # v3.0 Mode
            logger.info("Fetching from 18 v3.0 data sources...")
            results = fetch_all_v3_data_parallel()

            logger.info("Processing data (deduplication, clustering, timeline)...")
            logger.info(f"Clusters: {list(results['clusters'].keys())}")

            logger.info("Generating v3.0 report...")
            report = generate_v3_report(results, api_key)

        # Save
        logger.info("Saving report...")
        filepath = save_report(report, obsidian_path)

        logger.info(f"Report saved: {filepath}")
        logger.info("=" * 50)
        logger.info(f"Cloud927 v{mode} completed successfully!")
        logger.info("=" * 50)

        return 0

    except KeyboardInterrupt:
        logger.info("Cancelled")
        return 130
    except Exception as e:
        logger.exception(f"Error: {e}")
        return 1


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "v2"
    sys.exit(main(mode))
