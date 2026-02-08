"""Temporal Filter for dynamic freshness windows based on time of day."""

import logging
from datetime import datetime, timedelta
from typing import Literal

logger = logging.getLogger(__name__)


class TemporalFilter:
    """
    Dynamic freshness filter that adjusts time windows based on:
    - Time of day (business hours vs off-hours)
    - Day of week (weekday vs weekend)
    - Source type (news, github, paper, social)
    """

    def __init__(self):
        self._now = datetime.now()
        self._hour = self._now.hour
        self._is_weekend = self._now.weekday() in [5, 6]
        self._is_business_hours = 9 <= self._hour <= 18
        self._is_working_hours = 8 <= self._hour <= 22

    @property
    def now(self) -> datetime:
        """Current time (can be overridden for testing)."""
        return self._now

    @now.setter
    def now(self, value: datetime):
        """Set current time for testing."""
        self._now = value
        self._hour = value.hour
        self._is_weekend = value.weekday() in [5, 6]
        self._is_business_hours = 9 <= value.hour <= 18
        self._is_working_hours = 8 <= value.hour <= 22

    def get_window_seconds(
        self,
        source_type: Literal["news", "github", "paper", "social", "default"]
    ) -> int:
        """
        Get the freshness window in seconds based on source type and current time.

        Args:
            source_type: Type of the data source

        Returns:
            Freshness window in seconds
        """
        if source_type == "news":
            return self._get_news_window()
        elif source_type == "github":
            return self._get_github_window()
        elif source_type == "paper":
            return self._get_paper_window()
        elif source_type == "social":
            return self._get_social_window()
        else:
            return self._get_default_window()

    def _get_news_window(self) -> int:
        """Get window for news sources."""
        if self._is_weekend:
            # Longer window on weekends as news is slower
            return int(timedelta(hours=8).total_seconds())
        elif self._is_business_hours:
            # Shorter window during business hours for faster news
            return int(timedelta(hours=2).total_seconds())
        else:
            # Medium window during off-hours
            return int(timedelta(hours=6).total_seconds())

    def _get_github_window(self) -> int:
        """Get window for GitHub sources (always 24h)."""
        return int(timedelta(hours=24).total_seconds())

    def _get_paper_window(self) -> int:
        """Get window for academic papers (7 days)."""
        return int(timedelta(days=7).total_seconds())

    def _get_social_window(self) -> int:
        """Get window for social media (48h)."""
        if self._is_working_hours:
            return int(timedelta(hours=24).total_seconds())
        else:
            return int(timedelta(hours=48).total_seconds())

    def _get_default_window(self) -> int:
        """Default window (24h)."""
        return int(timedelta(hours=24).total_seconds())

    def is_fresh(
        self,
        timestamp: int,
        source_type: Literal["news", "github", "paper", "social", "default"] = "default"
    ) -> bool:
        """
        Check if a timestamp is within the freshness window.

        Args:
            timestamp: Unix timestamp to check
            source_type: Type of the data source

        Returns:
            True if the timestamp is fresh, False otherwise
        """
        window_seconds = self.get_window_seconds(source_type)
        current_time = int(self._now.timestamp())
        return (current_time - timestamp) <= window_seconds

    def filter_by_time(
        self,
        items: list[dict],
        source_type: Literal["news", "github", "paper", "social", "default"] = "default"
    ) -> list[dict]:
        """
        Filter items by freshness window.

        Args:
            items: List of items with 'timestamp' or 'time' field
            source_type: Type of the data source

        Returns:
            Filtered list of items within the freshness window
        """
        window_seconds = self.get_window_seconds(source_type)
        current_time = int(self._now.timestamp())

        filtered_items = []
        for item in items:
            # Get timestamp from various possible fields
            item_time = item.get("timestamp") or item.get("time") or item.get("created_at") or 0

            if isinstance(item_time, str):
                # Try to parse string timestamp
                try:
                    from dateutil import parser
                    dt = parser.parse(item_time)
                    item_time = int(dt.timestamp())
                except Exception:
                    continue

            if (current_time - item_time) <= window_seconds:
                filtered_items.append(item)

        logger.info(
            f"Temporal filter: {len(items)} -> {len(filtered_items)} items "
            f"(window: {window_seconds}s, type: {source_type})"
        )
        return filtered_items

    def get_time_info(self) -> dict:
        """Get current time information for debugging."""
        return {
            "datetime": self._now.isoformat(),
            "hour": self._hour,
            "is_weekend": self._is_weekend,
            "is_business_hours": self._is_business_hours,
            "is_working_hours": self._is_working_hours,
            "news_window_hours": self.get_window_seconds("news") / 3600,
            "github_window_hours": self.get_window_seconds("github") / 3600,
            "paper_window_hours": self.get_window_seconds("paper") / 3600 / 24,
            "social_window_hours": self.get_window_seconds("social") / 3600,
        }


if __name__ == "__main__":
    # Test the temporal filter
    filter = TemporalFilter()
    print("Current time info:")
    print(filter.get_time_info())
    print("\nFreshness windows:")
    print(f"  News: {filter.get_window_seconds('news') / 3600} hours")
    print(f"  GitHub: {filter.get_window_seconds('github') / 3600} hours")
    print(f"  Paper: {filter.get_window_seconds('paper') / 3600 / 24} days")
    print(f"  Social: {filter.get_window_seconds('social') / 3600} hours")
