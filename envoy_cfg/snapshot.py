"""Config snapshot: captures and restores config state for auditing and rollback."""

from __future__ import annotations

import copy
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Snapshot:
    """Immutable point-in-time capture of a config dict."""

    config: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    label: Optional[str] = None

    def __post_init__(self) -> None:
        # Ensure the stored config is a deep copy so it cannot be mutated.
        object.__setattr__(self, "config", copy.deepcopy(self.config))

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("Snapshot is immutable")


class SnapshotStore:
    """Stores an ordered history of config snapshots."""

    def __init__(self, max_history: int = 50) -> None:
        self._max_history = max_history
        self._snapshots: List[Snapshot] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def capture(self, config: Dict[str, Any], label: Optional[str] = None) -> Snapshot:
        """Take a snapshot of *config* and add it to the history."""
        snap = Snapshot(config=config, label=label)
        self._snapshots.append(snap)
        if len(self._snapshots) > self._max_history:
            self._snapshots.pop(0)
        return snap

    def latest(self) -> Optional[Snapshot]:
        """Return the most recent snapshot, or None if history is empty."""
        return self._snapshots[-1] if self._snapshots else None

    def previous(self) -> Optional[Snapshot]:
        """Return the second-most-recent snapshot, or None."""
        return self._snapshots[-2] if len(self._snapshots) >= 2 else None

    def history(self) -> List[Snapshot]:
        """Return a shallow copy of the snapshot history list."""
        return list(self._snapshots)

    def clear(self) -> None:
        """Discard all stored snapshots."""
        self._snapshots.clear()

    def __len__(self) -> int:
        return len(self._snapshots)
