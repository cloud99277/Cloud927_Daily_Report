"""Main entry point for the Daily Report Generator v2.0."""

import os
import sys
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from src.utils.logger import setup_logger
from src.fetchers.hn_fetcher import HNFetcher
from src.fetchers.hn_show_fetcher import HNShowFetcher
from src.fetchers.github_fetcher import GitHubFetcher
from src.fetchers.hf_api_fetcher import HuggingFaceAPIFetcher
from src.fetchers.ai_news_fetcher import AINewsFetcher
from src.fetchers.ph_fetcher import ProductHuntFetcher
from src.fetchers.reddit_fetcher import RedditAIFetcher
from src.fetchers.v2ex_fetcher import V2EXFetcher
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


def fetch_all_data_parallel() -> tuple:
    """Fetch all v2.0 data sources in parallel."""
    from src.utils.logger import setup_logger
    logger = setup_logger("fetcher")
    logger.info("Starting v2.0 parallel data fetch")

    # v2.0: 8 data sources
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
                    results[key] = future.result()
                    logger.info(f"{key.upper()} fetched: {len(results.get(key, [])) if isinstance(results.get(key), list) else 'dict'}")
                    break

    return (
        results.get("hn", {}),
        results.get("gh", {}),
        results.get("hf", []),
        results.get("ai_news", []),
        results.get("ph", []),
        results.get("reddit", []),
        results.get("v2ex", []),
        results.get("hn_show", {}),
    )


def generate_report(hn_data, gh_data, hf_data, ai_news_data, ph_data, reddit_data, v2ex_data, hn_show_data, api_key: str) -> str:
    """Generate v2.0 markdown report."""
    client = LLMClient(api_key=api_key)

    stories = hn_data.get("stories", [])
    gh_repos = gh_data.get("trending", []) + gh_data.get("ai_trending", [])
    showhn_posts = hn_show_data.get("posts", [])

    return client.generate_report(
        hn_data=stories,
        gh_data=gh_repos,
        hf_data=hf_data,
        showhn_data=showhn_posts,
        v2ex_data=v2ex_data,
        ai_news_data=ai_news_data,
        ph_data=ph_data,
        reddit_data=reddit_data,
    )


def save_report(content: str, vault_path: str) -> Path:
    """Save report to Obsidian vault."""
    writer = ObsidianWriter(vault_path=vault_path)
    return writer.write_report(content)


def main() -> int:
    """Main entry point."""
    logger = setup_logger("daily_report")

    try:
        logger.info("Loading environment variables")
        if not load_environment():
            logger.warning(".env not found")
        logger.info("=" * 50)
        logger.info("Starting Cloud927 v2.0 Daily Report Generator")
        logger.info("=" * 50)

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

        # Fetch v2.0 data
        logger.info("Fetching from 8 data sources...")
        hn_data, gh_data, hf_data, ai_news_data, ph_data, reddit_data, v2ex_data, hn_show_data = fetch_all_data_parallel()

        logger.info(f"HN: {len(hn_data.get('stories', []))} stories")
        logger.info(f"GitHub: {len(gh_data.get('trending', []))} trending, {len(gh_data.get('ai_trending', []))} AI")
        logger.info(f"HuggingFace: {len(hf_data)} papers")
        logger.info(f"AI News: {len(ai_news_data)} articles")
        logger.info(f"Product Hunt: {len(ph_data)} products")
        logger.info(f"Reddit: {len(reddit_data)} discussions")
        logger.info(f"V2EX: {len(v2ex_data)} posts")
        logger.info(f"Show HN: {len(hn_show_data.get('posts', []))} posts")

        # Generate v2.0 report
        logger.info("Generating v2.0 report...")
        report = generate_report(
            hn_data, gh_data, hf_data, ai_news_data, ph_data, reddit_data, v2ex_data, hn_show_data, api_key
        )

        # Save
        logger.info("Saving report...")
        filepath = save_report(report, obsidian_path)

        logger.info(f"✅ Report saved: {filepath}")
        logger.info("=" * 50)
        logger.info("Cloud927 v2.0 completed successfully!")
        logger.info("=" * 50)

        return 0

    except KeyboardInterrupt:
        logger.info("Cancelled")
        return 130
    except Exception as e:
        logger.exception(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
