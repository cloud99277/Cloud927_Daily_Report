"""Main entry point for the Daily Report generator."""

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
from src.fetchers.github_fetcher import GitHubFetcher
from src.fetchers.hf_fetcher import HuggingFaceFetcher
from src.fetchers.hf_api_fetcher import HuggingFaceAPIFetcher
from src.fetchers.v2ex_fetcher import V2EXFetcher
from src.fetchers.hn_show_fetcher import HNShowFetcher
from src.generator import LLMClient
from src.storage import ObsidianWriter


def load_environment() -> bool:
    """Load environment variables from .env file.

    Returns:
        True if successful, False otherwise.
    """
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        return True
    # Also check current working directory
    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists():
        load_dotenv(cwd_env)
        return True
    return False


def validate_obsidian_path(path: str) -> bool:
    """Validate that the Obsidian vault path exists.

    Args:
        path: Path to validate.

    Returns:
        True if valid, False otherwise.
    """
    return Path(path).exists() and Path(path).is_dir()


def fetch_hn_data() -> dict[str, Any]:
    """Fetch Hacker News data.

    Returns:
        Dictionary with HN data.
    """
    fetcher = HNFetcher()
    return fetcher.fetch()


def fetch_github_data() -> dict[str, Any]:
    """Fetch GitHub trending data.

    Returns:
        Dictionary with GitHub data including readme content for repos.
    """
    fetcher = GitHubFetcher()
    trending = fetcher.fetch_trending(language="python", limit=5, fetch_readme=True)
    ai_trending = fetcher.fetch_ai_trending(limit=5, fetch_readme=True)
    return {
        "trending": trending,
        "ai_trending": ai_trending,
    }


def fetch_hf_data() -> list[dict[str, Any]]:
    """Fetch HuggingFace data using API.

    Returns:
        List of HF papers/models.
    """
    fetcher = HuggingFaceAPIFetcher()
    return fetcher.fetch()


def fetch_v2ex_data() -> list[dict[str, Any]]:
    """Fetch V2EX discussions.

    Returns:
        List of V2EX posts.
    """
    fetcher = V2EXFetcher()
    return fetcher.fetch()


def fetch_hn_show_data() -> dict[str, Any]:
    """Fetch HN Show HN posts.

    Returns:
        Dictionary with Show HN posts.
    """
    fetcher = HNShowFetcher()
    return fetcher.fetch()


def fetch_all_data_parallel() -> tuple[dict, dict, dict, list, dict]:
    """Fetch all data sources in parallel.

    Returns:
        Tuple of (hn_data, gh_data, hf_data, v2ex_data, hn_show_data).
    """
    from src.utils.logger import setup_logger
    logger = setup_logger("fetcher")
    logger.info("Starting parallel data fetch")

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            "hn": executor.submit(fetch_hn_data),
            "gh": executor.submit(fetch_github_data),
            "hf": executor.submit(fetch_hf_data),
            "v2ex": executor.submit(fetch_v2ex_data),
            "hn_show": executor.submit(fetch_hn_show_data),
        }

        results = {}
        errors = {}

        for future in as_completed(futures.values()):
            try:
                # Find which key this future belongs to
                for key, f in futures.items():
                    if f is future or f == future:
                        results[key] = future.result()
                        logger.info(f"{key.upper()} data fetched successfully")
                        break
            except Exception as e:
                logger.error(f"Failed to fetch data: {e}")

    return (
        results.get("hn", {}),
        results.get("gh", {}),
        results.get("hf", []),
        results.get("v2ex", []),
        results.get("hn_show", {}),
    )


def generate_report(
    hn_data: dict, gh_data: dict, hf_data: list, v2ex_data: list, hn_show_data: dict, api_key: str
) -> str:
    """Generate the markdown report using LLM.

    Args:
        hn_data: Hacker News data.
        gh_data: GitHub data.
        hf_data: HuggingFace data.
        v2ex_data: V2EX discussions.
        hn_show_data: Show HN posts.
        api_key: Gemini API key.

    Returns:
        Generated markdown report.
    """
    client = LLMClient(api_key=api_key)

    # Prepare data in expected format
    stories = hn_data.get("stories", [])
    comments = hn_data.get("comments", [])

    # Flatten GitHub data
    gh_repos = gh_data.get("trending", []) + gh_data.get("ai_trending", [])

    report = client.generate_report(
        hn_data=stories,
        gh_data=gh_repos,
        hf_data=hf_data,
        showhn_data=hn_show_data.get("posts", []),
        v2ex_data=v2ex_data,
    )

    return report


def save_report(content: str, vault_path: str) -> Path:
    """Save the report to Obsidian vault.

    Args:
        content: Markdown content.
        vault_path: Path to Obsidian vault.

    Returns:
        Path to saved file.
    """
    writer = ObsidianWriter(vault_path=vault_path)
    filepath = writer.write_report(content)
    return filepath


def main() -> int:
    """Main entry point function.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    # Set up logging first
    logger = setup_logger("daily_report")

    try:
        # Load environment variables
        logger.info("Loading environment variables")
        if not load_environment():
            logger.warning(".env file not found, using existing environment variables")
        logger.info("=" * 50)
        logger.info("Starting Daily Report Generator")
        logger.info("=" * 50)

        # Get environment variables
        obsidian_path = os.environ.get("OBSIDIAN_VAULT_PATH", "")
        api_key = os.environ.get("GEMINI_API_KEY", "")
        log_level = os.environ.get("LOG_LEVEL", "INFO")

        # Validate OBSIDIAN_VAULT_PATH
        if not obsidian_path:
            logger.error("OBSIDIAN_VAULT_PATH environment variable is not set")
            return 1

        if not validate_obsidian_path(obsidian_path):
            logger.error(f"OBSIDIAN_VAULT_PATH does not exist or is not a directory: {obsidian_path}")
            return 1

        logger.info(f"Obsidian vault path: {obsidian_path}")
        logger.info(f"Log level: {log_level}")

        # Validate API key
        if not api_key:
            logger.error("GEMINI_API_KEY environment variable is not set")
            return 1

        # Fetch data in parallel
        logger.info("Fetching data from all sources...")
        hn_data, gh_data, hf_data, v2ex_data, hn_show_data = fetch_all_data_parallel()

        logger.info(f"HN: {len(hn_data.get('stories', []))} stories, {len(hn_data.get('comments', []))} comments")
        logger.info(f"GitHub: {len(gh_data.get('trending', []))} trending, {len(gh_data.get('ai_trending', []))} AI")
        logger.info(f"HuggingFace: {len(hf_data)} papers")
        logger.info(f"V2EX: {len(v2ex_data)} discussions")
        logger.info(f"Show HN: {len(hn_show_data.get('posts', []))} posts")

        # Generate report
        logger.info("Generating daily report...")
        report = generate_report(hn_data, gh_data, hf_data, v2ex_data, hn_show_data, api_key)

        # Save report
        logger.info("Saving report to Obsidian vault...")
        filepath = save_report(report, obsidian_path)

        logger.info(f"Report saved successfully: {filepath}")
        logger.info("=" * 50)
        logger.info("Daily Report Generator completed successfully")
        logger.info("=" * 50)

        return 0

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 130
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
