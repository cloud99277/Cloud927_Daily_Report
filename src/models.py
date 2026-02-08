"""Unified data models for Cloud927 Daily Report."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class NewsItem:
    """Unified news item model used across all fetchers and processors."""

    title: str
    url: str
    source: str
    timestamp: datetime
    content: str = ""
    score: float = 0
    source_type: str = ""
    language: str = "en"
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "timestamp": self.timestamp.timestamp() if isinstance(self.timestamp, datetime) else self.timestamp,
            "content": self.content,
            "score": self.score,
            "source_type": self.source_type,
            "language": self.language,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NewsItem":
        """Create NewsItem from dictionary."""
        ts = data.get("timestamp", 0)
        if isinstance(ts, (int, float)):
            ts = datetime.fromtimestamp(ts) if ts > 0 else datetime.now()
        elif isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts)
            except ValueError:
                ts = datetime.now()

        return cls(
            title=data.get("title", ""),
            url=data.get("url", ""),
            source=data.get("source", ""),
            timestamp=ts,
            content=data.get("content", ""),
            score=float(data.get("score", 0) or 0),
            source_type=data.get("source_type", ""),
            language=data.get("language", "en"),
            metadata=data.get("metadata", {}),
        )
