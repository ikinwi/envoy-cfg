"""Redactor module for masking sensitive config values before export or logging."""

import re
from typing import Any, Dict, List, Optional

DEFAULT_SENSITIVE_PATTERNS = [
    re.compile(r"password", re.IGNORECASE),
    re.compile(r"secret", re.IGNORECASE),
    re.compile(r"token", re.IGNORECASE),
    re.compile(r"api_key", re.IGNORECASE),
    re.compile(r"private_key", re.IGNORECASE),
    re.compile(r"auth", re.IGNORECASE),
]

REDACTED_PLACEHOLDER = "**REDACTED**"


class ConfigRedactor:
    """Masks sensitive keys in a config dictionary based on key name patterns."""

    def __init__(
        self,
        extra_patterns: Optional[List[str]] = None,
        placeholder: str = REDACTED_PLACEHOLDER,
    ) -> None:
        self._patterns: List[re.Pattern] = list(DEFAULT_SENSITIVE_PATTERNS)
        if extra_patterns:
            for pat in extra_patterns:
                self._patterns.append(re.compile(pat, re.IGNORECASE))
        self.placeholder = placeholder

    def _is_sensitive(self, key: str) -> bool:
        return any(pat.search(key) for pat in self._patterns)

    def redact(self, config: Dict[str, Any], _path: str = "") -> Dict[str, Any]:
        """Return a new dict with sensitive values replaced by the placeholder."""
        result: Dict[str, Any] = {}
        for key, value in config.items():
            full_key = f"{_path}.{key}" if _path else key
            if isinstance(value, dict):
                result[key] = self.redact(value, _path=full_key)
            elif self._is_sensitive(key):
                result[key] = self.placeholder
            else:
                result[key] = value
        return result

    def add_pattern(self, pattern: str) -> None:
        """Register an additional sensitive key pattern at runtime."""
        self._patterns.append(re.compile(pattern, re.IGNORECASE))
