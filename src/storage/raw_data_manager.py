"""Raw Data Manager for incremental fetching."""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class RawDataManager:
    """
    Manage raw data storage and incremental fetching.

    Features:
    - Save raw data with timestamps
    - Track last fetch times
    - Check if fetch is needed based on intervals
    - Load historical data
    """

    def __init__(
        self,
        data_dir: str = "data/raw",
        state_file: str = "data/fetch_state.json"
    ):
        """
        Initialize the raw data manager.

        Args:
            data_dir: Directory to store raw data
            state_file: File to store fetch state
        """
        self.data_dir = Path(data_dir)
        self.state_file = Path(state_file)
        self.state = self._load_state()

        # Create directories
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Default fetch intervals (in seconds)
        self.default_intervals = {
            "high_frequency": 3600,      # 1 hour
            "medium_frequency": 14400,   # 4 hours
            "low_frequency": 43200,      # 12 hours
            "very_low_frequency": 86400, # 24 hours
        }

    def _load_state(self) -> dict:
        """Load state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load fetch state: {e}")

        return {"last_fetch": {}, "source_info": {}}

    def _save_state(self):
        """Save state to file."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
            logger.debug("Saved fetch state")
        except Exception as e:
            logger.error(f"Failed to save fetch state: {e}")

    def get_interval(self, source: str) -> int:
        """
        Get the fetch interval for a source.

        Args:
            source: Name of the data source

        Returns:
            Interval in seconds
        """
        # Check if source has custom interval in state
        if source in self.state.get("source_info", {}):
            return self.state["source_info"][source].get("interval", self.default_intervals["medium_frequency"])

        return self.default_intervals["medium_frequency"]

    def set_interval(self, source: str, interval: int):
        """
        Set the fetch interval for a source.

        Args:
            source: Name of the data source
            interval: Interval in seconds
        """
        if "source_info" not in self.state:
            self.state["source_info"] = {}

        self.state["source_info"][source] = self.state["source_info"].get(source, {})
        self.state["source_info"][source]["interval"] = interval
        self._save_state()

    def should_fetch(self, source: str, force: bool = False) -> bool:
        """
        Check if a source should be fetched.

        Args:
            source: Name of the data source
            force: Force fetch regardless of interval

        Returns:
            True if fetch is needed
        """
        if force:
            logger.info(f"Force fetch for {source}")
            return True

        last_fetch = self.state["last_fetch"].get(source)

        if not last_fetch:
            logger.info(f"Never fetched {source}, should fetch")
            return True

        interval = self.get_interval(source)
        time_since_last = time.time() - last_fetch

        should = time_since_last > interval
        if should:
            logger.info(
                f"{source}: {time_since_last:.0f}s since last fetch, "
                f"interval is {interval}s, should fetch"
            )
        else:
            logger.debug(
                f"{source}: {time_since_last:.0f}s since last fetch, "
                f"interval is {interval}s, skip"
            )

        return should

    def save_raw(
        self,
        source: str,
        data: list[dict] | dict,
        metadata: dict | None = None
    ) -> Path:
        """
        Save raw data to a timestamped file.

        Args:
            source: Name of the data source
            data: Data to save
            metadata: Optional metadata

        Returns:
            Path to the saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        source_dir = self.data_dir / source
        source_dir.mkdir(parents=True, exist_ok=True)

        filepath = source_dir / f"{timestamp}.json"

        save_data = {
            "timestamp": timestamp,
            "source": source,
            "created_at": datetime.now().isoformat(),
            "data": data,
            "metadata": metadata or {}
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)

        # Update last fetch time
        self.state["last_fetch"][source] = int(time.time())
        self._save_state()

        logger.info(f"Saved raw data for {source}: {filepath}")
        return filepath

    def update_fetch_time(self, source: str):
        """
        Update the last fetch time for a source.

        Args:
            source: Name of the data source
        """
        self.state["last_fetch"][source] = int(time.time())
        self._save_state()

    def get_history(
        self,
        source: str,
        limit: int = 10
    ) -> list[dict]:
        """
        Get historical data for a source.

        Args:
            source: Name of the data source
            limit: Maximum number of historical files to return

        Returns:
            List of historical data entries
        """
        source_dir = self.data_dir / source

        if not source_dir.exists():
            return []

        files = sorted(source_dir.glob("*.json"), reverse=True)[:limit]

        history = []
        for filepath in files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    history.append(data)
            except Exception as e:
                logger.error(f"Failed to load {filepath}: {e}")

        return history

    def get_latest(
        self,
        source: str
    ) -> dict | None:
        """
        Get the latest data for a source.

        Args:
            source: Name of the data source

        Returns:
            Latest data entry or None
        """
        history = self.get_history(source, limit=1)
        return history[0] if history else None

    def get_state(self) -> dict:
        """Get the current state."""
        return {
            "last_fetch": self.state.get("last_fetch", {}),
            "source_info": self.state.get("source_info", {}),
            "data_dir": str(self.data_dir),
        }

    def cleanup_old_data(
        self,
        source: str | None = None,
        keep_count: int = 10
    ):
        """
        Clean up old raw data files.

        Args:
            source: Specific source to clean (None for all)
            keep_count: Number of files to keep
        """
        if source:
            sources = [source]
        else:
            sources = [d.name for d in self.data_dir.iterdir() if d.is_dir()]

        for source_name in sources:
            source_dir = self.data_dir / source_name

            if not source_dir.exists():
                continue

            files = sorted(source_dir.glob("*.json"))

            if len(files) > keep_count:
                to_delete = files[keep_count:]

                for filepath in to_delete:
                    filepath.unlink()
                    logger.info(f"Deleted old data: {filepath}")


if __name__ == "__main__":
    # Test the raw data manager
    manager = RawDataManager()

    print("State:", manager.get_state())

    # Check if should fetch
    print("\nShould fetch hn:", manager.should_fetch("hn"))
    print("Should fetch new_source:", manager.should_fetch("new_source"))

    # Save some test data
    test_data = [{"title": "Test item", "value": 1}]
    filepath = manager.save_raw("test_source", test_data)
    print(f"\nSaved to: {filepath}")

    # Check if should fetch now
    print("Should fetch test_source:", manager.should_fetch("test_source"))

    # Get history
    history = manager.get_history("test_source")
    print(f"\nHistory: {len(history)} entries")
