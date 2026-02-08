"""Storage module for Obsidian vault operations."""

import os
from datetime import date
from pathlib import Path
from typing import Optional


class ObsidianWriter:
    """Handles writing daily reports to an Obsidian vault."""

    def __init__(self, vault_path: Optional[str] = None) -> None:
        """Initialize the ObsidianWriter.

        Args:
            vault_path: Path to the Obsidian vault. If not provided,
                       reads from OBSIDIAN_VAULT_PATH environment variable.

        Raises:
            ValueError: If no vault path is provided and environment variable is not set.
        """
        if vault_path is None:
            vault_path = os.environ.get("OBSIDIAN_VAULT_PATH")

        if not vault_path:
            raise ValueError("OBSIDIAN_VAULT_PATH not set in environment or passed as argument")

        self.vault_path = Path(vault_path)
        self._validate_vault_path()

    def _validate_vault_path(self) -> None:
        """Validate that the vault path exists and is a directory.

        Raises:
            ValueError: If the vault path does not exist or is not a directory.
        """
        if not self.vault_path.exists():
            raise ValueError(f"Obsidian vault path does not exist: {self.vault_path}")

        if not self.vault_path.is_dir():
            raise ValueError(f"Obsidian vault path is not a directory: {self.vault_path}")

    def _get_filename(self, report_date: date) -> str:
        """Generate the filename for a report.

        Args:
            report_date: The date of the report.

        Returns:
            The filename in YYYY-MM-DD.md format.
        """
        return f"{report_date.isoformat()}.md"

    def _get_filepath(self, report_date: date) -> Path:
        """Get the full filepath for a report with monthly subfolders.

        Format: vault_path/{MM}_Daily_Reports/YYYY-MM/YYYY-MM-DD.md
        Example: Obsidian/10_Daily_Reports/2026-02/2026-02-08.md

        Args:
            report_date: The date of the report.

        Returns:
            The full path to the report file.
        """
        month_folder = f"{report_date.month:02d}_Daily_Reports"
        year_month_folder = report_date.strftime("%Y-%m")
        filename = self._get_filename(report_date)

        # Create full path with monthly subfolders
        full_path = self.vault_path / month_folder / year_month_folder / filename

        # Ensure parent directories exist
        full_path.parent.mkdir(parents=True, exist_ok=True)

        return full_path

    def write_report(self, content: str, report_date: Optional[date] = None) -> Path:
        """Write a daily report to the Obsidian vault.

        Args:
            content: The markdown content to write.
            report_date: The date of the report. Defaults to today.

        Returns:
            The path to the written file.

        Raises:
            OSError: If the file cannot be written.
        """
        if report_date is None:
            report_date = date.today()

        filepath = self._get_filepath(report_date)

        try:
            filepath.write_text(content, encoding="utf-8")
        except OSError as e:
            raise OSError(f"Failed to write report to {filepath}: {e}") from e

        return filepath

    def report_exists(self, report_date: Optional[date] = None) -> bool:
        """Check if a report already exists for the given date.

        Args:
            report_date: The date of the report. Defaults to today.

        Returns:
            True if the report file exists, False otherwise.
        """
        if report_date is None:
            report_date = date.today()

        return self._get_filepath(report_date).exists()
