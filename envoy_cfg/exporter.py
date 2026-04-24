"""Export resolved config to various formats: dict, JSON, dotenv, YAML."""

import json
from typing import Any, Dict, Optional


class ConfigExporter:
    """Exports a resolved config dictionary to multiple output formats."""

    def __init__(self, config: Dict[str, Any]):
        """
        Args:
            config: A flat or nested dictionary of resolved config values.
        """
        self._config = config

    def to_dict(self) -> Dict[str, Any]:
        """Return the raw config dictionary."""
        return dict(self._config)

    def to_json(self, indent: int = 2) -> str:
        """Serialize config to a JSON string.

        Args:
            indent: Number of spaces for JSON indentation.

        Returns:
            Pretty-printed JSON string.
        """
        return json.dumps(self._config, indent=indent, default=str)

    def to_dotenv(self, prefix: Optional[str] = None) -> str:
        """Serialize config to dotenv format (KEY=value lines).

        Args:
            prefix: Optional prefix to prepend to every key (e.g. 'APP').

        Returns:
            A string in dotenv format.
        """
        lines = []
        for key, value in self._config.items():
            env_key = f"{prefix.upper()}_{key.upper()}" if prefix else key.upper()
            # Quote values that contain spaces or special characters
            str_value = str(value)
            if any(c in str_value for c in (" ", "#", "=", "\n")):
                str_value = f'"{str_value}"'
            lines.append(f"{env_key}={str_value}")
        return "\n".join(lines)

    def to_yaml(self) -> str:
        """Serialize config to a simple YAML-like string (no external deps).

        Returns:
            A YAML-formatted string.
        """
        lines = []
        for key, value in self._config.items():
            if isinstance(value, str):
                lines.append(f"{key}: \"{value}\"")
            elif isinstance(value, bool):
                lines.append(f"{key}: {str(value).lower()}")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)
