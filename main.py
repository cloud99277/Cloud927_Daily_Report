"""Cloud927 Daily Report Generator - Main Entry Point."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.utils.logger import setup_logger


def load_environment() -> bool:
    """Load environment variables from .env file."""
    for path in [Path(__file__).parent / ".env", Path.cwd() / ".env"]:
        if path.exists():
            load_dotenv(path, override=True)
            return True
    return False


def main() -> int:
    """Run the Cloud927 pipeline."""
    logger = setup_logger("cloud927")

    try:
        load_environment()

        obsidian_path = os.environ.get("OBSIDIAN_VAULT_PATH", "")
        if not obsidian_path or not Path(obsidian_path).is_dir():
            logger.error("OBSIDIAN_VAULT_PATH not set or invalid")
            return 1

        from src.pipeline import Pipeline

        pipeline = Pipeline(obsidian_vault_path=obsidian_path)
        pipeline.run()

        logger.info("Cloud927 completed successfully!")
        return 0

    except KeyboardInterrupt:
        logger.info("Cancelled")
        return 130
    except Exception as e:
        logger.exception(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
