"""Configuration loader for Cloud927 v3.0."""

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager that loads from config.yaml."""

    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self.load()

    def load(self, config_path: str | None = None):
        """Load configuration from YAML file."""
        if config_path is None:
            # Try multiple possible locations
            possible_paths = [
                Path(__file__).parent.parent.parent / "config.yaml",  # project root
                Path(__file__).parent.parent / "config.yaml",          # parent of src
                Path.cwd() / "config.yaml",                            # current directory
            ]
            config_file = None
            for path in possible_paths:
                if path.exists():
                    config_file = path
                    break
            if config_file is None:
                logger.warning(f"Config file not found in any location")
                self._config = {}
                return
        else:
            config_file = Path(config_path)

        if not config_file.exists():
            logger.warning(f"Config file not found: {config_file}")
            self._config = {}
            return

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f)
            logger.info(f"Loaded config from: {config_file}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self._config = {}

    def reload(self):
        """Reload configuration."""
        self._config = None
        self.load()

    @property
    def app(self) -> dict:
        """Get app configuration."""
        return self._config.get("app", {})

    @property
    def llm(self) -> dict:
        """Get LLM configuration."""
        return self._config.get("llm", {})

    @property
    def sources(self) -> dict:
        """Get all data source configurations."""
        return self._config.get("sources", {})

    @property
    def fetcher_groups(self) -> dict:
        """Get fetcher group configurations."""
        return self._config.get("fetcher_groups", {})

    @property
    def processing(self) -> dict:
        """Get processing configuration."""
        return self._config.get("processing", {})

    @property
    def output(self) -> dict:
        """Get output configuration."""
        return self._config.get("output", {})

    @property
    def source_priority(self) -> dict:
        """Get source priority ranking."""
        return self._config.get("source_priority", {})

    def get_source_config(self, source_name: str) -> dict | None:
        """Get configuration for a specific source."""
        return self.sources.get(source_name)

    def is_source_enabled(self, source_name: str) -> bool:
        """Check if a source is enabled."""
        config = self.get_source_config(source_name)
        return config.get("enabled", True) if config else True

    def get_source_interval(self, source_name: str) -> int:
        """Get fetch interval for a source in seconds."""
        config = self.get_source_config(source_name)
        if config:
            interval_minutes = config.get("fetch_interval_minutes", 120)
            return interval_minutes * 60
        return 14400  # Default 4 hours

    def get_source_category(self, source_name: str) -> str:
        """Get the category/group for a source."""
        config = self.get_source_config(source_name)
        return config.get("category", "default") if config else "default"

    def get_fetcher_group_sources(self, group_name: str) -> list[str]:
        """Get sources in a fetcher group."""
        group = self.fetcher_groups.get(group_name, {})
        return group.get("sources", [])


# Global config instance
config = Config()
