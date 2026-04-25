"""ConfigProfiler: Detects unused, duplicate, and deprecated config keys."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


def _flatten_keys(d: Dict[str, Any], prefix: str = "") -> Set[str]:
    """Recursively collect all dotted key paths from a nested dict."""
    keys: Set[str] = set()
    for k, v in d.items():
        full_key = f"{prefix}.{k}" if prefix else k
        keys.add(full_key)
        if isinstance(v, dict):
            keys |= _flatten_keys(v, full_key)
    return keys


@dataclass
class ProfileReport:
    unused_keys: List[str] = field(default_factory=list)
    duplicate_keys: List[str] = field(default_factory=list)
    deprecated_keys: List[str] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return bool(self.unused_keys or self.duplicate_keys or self.deprecated_keys)

    def summary(self) -> str:
        lines = ["ConfigProfiler Report:"]
        if self.unused_keys:
            lines.append(f"  Unused keys ({len(self.unused_keys)}): {self.unused_keys}")
        if self.duplicate_keys:
            lines.append(f"  Duplicate keys ({len(self.duplicate_keys)}): {self.duplicate_keys}")
        if self.deprecated_keys:
            lines.append(f"  Deprecated keys ({len(self.deprecated_keys)}): {self.deprecated_keys}")
        if not self.has_issues:
            lines.append("  No issues found.")
        return "\n".join(lines)


class ConfigProfiler:
    """Analyses a config dict against a known schema and optional deprecation list."""

    def __init__(
        self,
        schema_keys: Optional[Set[str]] = None,
        deprecated_keys: Optional[List[str]] = None,
    ) -> None:
        self._schema_keys: Set[str] = schema_keys or set()
        self._deprecated_keys: List[str] = deprecated_keys or []

    def profile(self, config: Dict[str, Any]) -> ProfileReport:
        """Run all profiling checks and return a ProfileReport."""
        present_keys = _flatten_keys(config)

        unused = sorted(self._schema_keys - present_keys) if self._schema_keys else []
        deprecated = sorted(k for k in self._deprecated_keys if k in present_keys)
        duplicate = self._find_duplicates(config)

        return ProfileReport(
            unused_keys=unused,
            duplicate_keys=duplicate,
            deprecated_keys=deprecated,
        )

    def _find_duplicates(self, config: Dict[str, Any]) -> List[str]:
        """Detect keys that appear more than once at the same nesting level."""
        seen: Dict[str, int] = {}
        self._count_keys(config, seen)
        return sorted(k for k, count in seen.items() if count > 1)

    def _count_keys(self, d: Dict[str, Any], seen: Dict[str, int], prefix: str = "") -> None:
        for k, v in d.items():
            full_key = f"{prefix}.{k}" if prefix else k
            seen[full_key] = seen.get(full_key, 0) + 1
            if isinstance(v, dict):
                self._count_keys(v, seen, full_key)
