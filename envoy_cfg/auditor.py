"""Config auditor: tracks changes between config snapshots and emits diff reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ConfigDiff:
    """Represents a single key-level difference between two configs."""

    key: str
    old_value: Any
    new_value: Any
    change_type: str  # 'added', 'removed', 'modified'

    def __repr__(self) -> str:
        return f"ConfigDiff({self.change_type!r}, key={self.key!r}, {self.old_value!r} -> {self.new_value!r})"


@dataclass
class AuditReport:
    """Full diff report between two config snapshots."""

    diffs: List[ConfigDiff] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.diffs)

    @property
    def added(self) -> List[ConfigDiff]:
        return [d for d in self.diffs if d.change_type == "added"]

    @property
    def removed(self) -> List[ConfigDiff]:
        return [d for d in self.diffs if d.change_type == "removed"]

    @property
    def modified(self) -> List[ConfigDiff]:
        return [d for d in self.diffs if d.change_type == "modified"]

    def summary(self) -> str:
        return (
            f"AuditReport: {len(self.added)} added, "
            f"{len(self.removed)} removed, "
            f"{len(self.modified)} modified"
        )


def _flatten(obj: Any, prefix: str = "") -> Dict[str, Any]:
    """Flatten a nested dict into dot-separated key paths."""
    items: Dict[str, Any] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            full_key = f"{prefix}.{k}" if prefix else k
            items.update(_flatten(v, full_key))
    else:
        items[prefix] = obj
    return items


class ConfigAuditor:
    """Compares two config snapshots and produces an AuditReport."""

    def diff(
        self,
        old: Dict[str, Any],
        new: Dict[str, Any],
    ) -> AuditReport:
        old_flat = _flatten(old)
        new_flat = _flatten(new)

        old_keys = set(old_flat)
        new_keys = set(new_flat)

        diffs: List[ConfigDiff] = []

        for key in sorted(new_keys - old_keys):
            diffs.append(ConfigDiff(key, None, new_flat[key], "added"))

        for key in sorted(old_keys - new_keys):
            diffs.append(ConfigDiff(key, old_flat[key], None, "removed"))

        for key in sorted(old_keys & new_keys):
            if old_flat[key] != new_flat[key]:
                diffs.append(ConfigDiff(key, old_flat[key], new_flat[key], "modified"))

        return AuditReport(diffs=diffs)
