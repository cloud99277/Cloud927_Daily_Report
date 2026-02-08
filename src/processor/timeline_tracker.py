"""Entity tracking for monitoring developments over time."""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TimelineTracker:
    """
    Track entities (companies, products, people) over time.
    Detects new appearances, updates, and ongoing developments.
    """

    # Default entities to track
    DEFAULT_ENTITIES = [
        "OpenAI", "Anthropic", "Google", "Meta", "Microsoft",
        "字节跳动", "阿里巴巴", "百度", "腾讯",
        "GPT-4", "Claude", "Gemini", "LLaMA",
        "ChatGPT", "Claude AI", "Bard", "Copilot"
    ]

    def __init__(
        self,
        state_file: str = "data/timeline_state.json",
        entities: list[str] | None = None
    ):
        """
        Initialize the timeline tracker.

        Args:
            state_file: Path to store the state file
            entities: List of entities to track (default: DEFAULT_ENTITIES)
        """
        self.state_file = Path(state_file)
        self.entities = entities or self.DEFAULT_ENTITIES
        self.state = self._load_state()

    def _load_state(self) -> dict:
        """Load state from file or return empty state."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    logger.info(f"Loaded timeline state: {len(data.get('entities', {}))} entities")
                    return data
            except Exception as e:
                logger.warning(f"Failed to load timeline state: {e}")

        return {
            "entities": {},
            "last_update": None,
            "version": "3.0.0"
        }

    def _save_state(self):
        """Save state to file."""
        self.state["last_update"] = self._get_current_timestamp()
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
            logger.debug("Saved timeline state")
        except Exception as e:
            logger.error(f"Failed to save timeline state: {e}")

    def _get_current_timestamp(self) -> int:
        """Get current Unix timestamp."""
        import time
        return int(time.time())

    def _extract_entities(self, text: str) -> list[str]:
        """Extract tracked entities from text."""
        found_entities = []
        text_lower = text.lower()

        for entity in self.entities:
            if entity.lower() in text_lower:
                found_entities.append(entity)

        return found_entities

    def _get_entity_state(self, entity: str) -> dict:
        """Get or create state for an entity."""
        if entity not in self.state["entities"]:
            self.state["entities"][entity] = {
                "first_seen": self._get_current_timestamp(),
                "last_seen": None,
                "mentions": 0,
                "status": "new",
                "events": [],
                "keywords": set()
            }

        return self.state["entities"][entity]

    def track(self, items: list[dict]) -> dict:
        """
        Track entities in new items and detect changes.

        Args:
            items: List of new items to process

        Returns:
            Dict with 'new', 'updated', 'ongoing' entity statuses
        """
        logger.info(f"Tracking entities in {len(items)} items")

        timeline = {
            "new": [],       # First time seeing this entity
            "updated": [],   # Entity with new developments
            "ongoing": [],   # Entity being discussed but no new updates
            "entities_found": set()
        }

        # First pass: extract entities from all items
        for item in items:
            title = item.get("title", "")
            content = item.get("content", "") or item.get("description", "")
            url = item.get("url", "")
            timestamp = item.get("timestamp", 0) or item.get("time", 0)
            source = item.get("source", "")

            text = f"{title} {content}"
            found_entities = self._extract_entities(text)

            for entity in found_entities:
                timeline["entities_found"].add(entity)
                entity_state = self._get_entity_state(entity)

                # Determine the context of this mention
                context = self._extract_context(item)

                event = {
                    "timestamp": timestamp,
                    "source": source,
                    "title": title,
                    "url": url,
                    "context": context
                }

                if entity_state["mentions"] == 0:
                    # First mention - new entity
                    entity_state["status"] = "new"
                    entity_state["last_seen"] = timestamp
                    entity_state["mentions"] = 1
                    entity_state["events"].append(event)

                    timeline["new"].append({
                        "entity": entity,
                        "first_event": event
                    })
                else:
                    # Already seen - check if this is an update
                    entity_state["mentions"] += 1

                    # Check if this event is significantly different
                    is_update = self._is_meaningful_update(entity_state, event)

                    if is_update:
                        entity_state["status"] = "updated"
                        entity_state["last_seen"] = timestamp
                        entity_state["events"].append(event)

                        # Keep only last 10 events
                        if len(entity_state["events"]) > 10:
                            entity_state["events"] = entity_state["events"][-10:]

                        timeline["updated"].append({
                            "entity": entity,
                            "previous_event": entity_state["events"][-2] if len(entity_state["events"]) > 1 else None,
                            "new_event": event
                        })
                    else:
                        # Just ongoing discussion
                        entity_state["last_seen"] = timestamp
                        timeline["ongoing"].append({
                            "entity": entity,
                            "event": event
                        })

        # Update state for entities not mentioned in this batch
        current_time = self._get_current_timestamp()
        for entity, entity_state in self.state["entities"].items():
            if entity not in timeline["entities_found"]:
                entity_state["status"] = "dormant"

        # Save state
        self._save_state()

        # Convert sets to lists for JSON serialization
        timeline["entities_found"] = list(timeline["entities_found"])

        # Log summary
        logger.info(
            f"Timeline tracking complete: "
            f"{len(timeline['new'])} new, "
            f"{len(timeline['updated'])} updated, "
            f"{len(timeline['ongoing'])} ongoing"
        )

        return timeline

    def _extract_context(self, item: dict) -> str:
        """Extract context/keywords from an item."""
        title = item.get("title", "").lower()
        content = item.get("content", "") or item.get("description", "")

        # Extract key phrases
        context_parts = []

        # Check for action keywords
        action_keywords = {
            "releases": "release",
            "announces": "announcement",
            "launches": "launch",
            "releases": "release",
            "unveils": "unveil",
            "releases": "release",
            "updates": "update",
            "releases": "release",
            "raises": "funding",
            "acquires": "acquisition",
            "research": "research",
            "study": "study",
            "finds": "finding",
            "discovers": "discovery"
        }

        for keyword, context in action_keywords.items():
            if keyword in title:
                context_parts.append(context)
                break

        return " | ".join(context_parts) if context_parts else "discussion"

    def _is_meaningful_update(
        self,
        entity_state: dict,
        new_event: dict
    ) -> bool:
        """Check if a new event represents a meaningful update."""
        events = entity_state.get("events", [])

        if not events:
            return True

        last_event = events[-1]

        # Check if from a different source
        if new_event.get("source") != last_event.get("source"):
            return True

        # Check if title is significantly different
        from difflib import SequenceMatcher
        similarity = SequenceMatcher(
            None,
            new_event.get("title", ""),
            last_event.get("title", "")
        ).ratio()

        # If less than 70% similar, it's likely a new development
        return similarity < 0.70

    def get_entity_status(self, entity: str) -> dict | None:
        """Get the current status of an entity."""
        if entity not in self.state["entities"]:
            return None

        return self.state["entities"][entity]

    def get_all_statuses(self) -> dict:
        """Get status of all tracked entities."""
        return self.state["entities"]

    def reset_entity(self, entity: str):
        """Reset tracking for an entity (start fresh)."""
        if entity in self.state["entities"]:
            del self.state["entities"][entity]
            self._save_state()
            logger.info(f"Reset tracking for entity: {entity}")

    def add_entity(self, entity: str):
        """Add a new entity to track."""
        if entity not in self.entities:
            self.entities.append(entity)
            logger.info(f"Added entity to track: {entity}")


if __name__ == "__main__":
    # Test timeline tracking
    tracker = TimelineTracker()

    test_items = [
        {
            "title": "OpenAI releases GPT-5",
            "url": "https://openai.com/gpt5",
            "timestamp": 1000000,
            "source": "openai.com"
        },
        {
            "title": "OpenAI announces pricing for GPT-5",
            "url": "https://openai.com/pricing",
            "timestamp": 1000100,
            "source": "openai.com"
        },
        {
            "title": "Google unveils Gemini Ultra",
            "url": "https://google.com/gemini",
            "timestamp": 1000200,
            "source": "google.com"
        },
        {
            "title": "Anthropic releases Claude 3",
            "url": "https://anthropic.com/claude3",
            "timestamp": 1000300,
            "source": "anthropic.com"
        }
    ]

    timeline = tracker.track(test_items)
    print("\nTimeline Results:")
    print(f"New entities: {len(timeline['new'])}")
    for item in timeline['new']:
        print(f"  - {item['entity']}: {item['first_event']['title'][:40]}")

    print(f"\nUpdated entities: {len(timeline['updated'])}")
    for item in timeline['updated']:
        print(f"  - {item['entity']}: {item['new_event']['title'][:40]}")

    print(f"\nOngoing: {len(timeline['ongoing'])}")
