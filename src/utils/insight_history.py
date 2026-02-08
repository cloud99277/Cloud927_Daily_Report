"""Insight history tracker to avoid duplicate deep dives."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class InsightHistory:
    """Track insight topics to avoid repetition across daily reports."""

    def __init__(self, history_file: str = "data/insight_history.json", keep_days: int = 7):
        """Initialize insight history tracker.

        Args:
            history_file: Path to JSON file storing insight history
            keep_days: Number of days to keep in history (default: 7)
        """
        self.history_file = Path(history_file)
        self.keep_days = keep_days
        self.history: Dict[str, List[str]] = {}
        self._load_history()

    def _load_history(self) -> None:
        """Load insight history from JSON file."""
        if not self.history_file.exists():
            logger.info(f"No history file found at {self.history_file}, starting fresh")
            self.history = {}
            return

        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                self.history = json.load(f)
            logger.info(f"Loaded insight history: {len(self.history)} days")
        except Exception as e:
            logger.error(f"Failed to load insight history: {e}")
            self.history = {}

    def _save_history(self) -> None:
        """Save insight history to JSON file."""
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved insight history: {len(self.history)} days")
        except Exception as e:
            logger.error(f"Failed to save insight history: {e}")

    def _cleanup_old_entries(self) -> None:
        """Remove entries older than keep_days."""
        cutoff_date = (datetime.now() - timedelta(days=self.keep_days)).strftime("%Y-%m-%d")
        
        old_dates = [date for date in self.history.keys() if date < cutoff_date]
        for date in old_dates:
            del self.history[date]
        
        if old_dates:
            logger.info(f"Cleaned up {len(old_dates)} old entries")

    def get_recent_topics(self, days: int = 3) -> List[str]:
        """Get insight topics from recent N days.

        Args:
            days: Number of recent days to retrieve (default: 3)

        Returns:
            List of insight topic titles from recent days
        """
        recent_topics = []
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        for date, topics in sorted(self.history.items(), reverse=True):
            if date >= cutoff_date:
                recent_topics.extend(topics)
        
        return recent_topics

    def add_topics(self, date_str: str, topics: List[str]) -> None:
        """Add insight topics for a specific date.

        Args:
            date_str: Date in YYYY-MM-DD format
            topics: List of insight topic titles
        """
        self.history[date_str] = topics
        self._cleanup_old_entries()
        self._save_history()
        logger.info(f"Added {len(topics)} topics for {date_str}")

    @staticmethod
    def extract_insight_topics(report: str) -> List[str]:
        """Extract insight topic titles from report content.

        Args:
            report: Full report markdown content

        Returns:
            List of insight topic titles
        """
        import re

        topics = []

        # Match patterns like "### 🔍 洞察一：xxx" or "### 话题 1: xxx"
        patterns = [
            r'###\s*🔍?\s*洞察[一二三四五]\s*[：:]\s*(.+)',
            r'###\s*话题\s*\d+\s*[：:]\s*(.+)',
            r'###\s*深度洞察\s*[-–—]\s*(.+)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, report)
            topics.extend([m.strip() for m in matches])

        return topics
