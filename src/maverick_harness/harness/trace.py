import json
from datetime import UTC, datetime
from pathlib import Path

from maverick_harness.harness.events import HarnessEvent


class TraceLogger:
    """Append-only JSONL trajectory logger for HarnessEvents."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log_event(self, event: HarnessEvent) -> None:
        """Append one timestamped event record as a JSON line."""
        record = {
            "ts": datetime.now(UTC).isoformat(),
            "event_type": type(event).__name__,
            **event.model_dump(),
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")