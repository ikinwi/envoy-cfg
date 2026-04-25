"""ConfigRenderer: render config values as formatted templates for display or export."""

from typing import Any, Dict, Optional
import json


class RenderError(Exception):
    """Raised when rendering fails due to unsupported format or bad input."""
    pass


class ConfigRenderer:
    """Renders a flat or nested config dict into various human-readable formats."""

    SUPPORTED_FORMATS = ("table", "json", "ini", "shell")

    def __init__(self, config: Dict[str, Any], redact_keys: Optional[list] = None):
        self._config = config
        self._redact_keys = [k.lower() for k in (redact_keys or [])]

    def _should_redact(self, key: str) -> bool:
        return any(r in key.lower() for r in self._redact_keys)

    def _flatten(self, data: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        result = {}
        for k, v in data.items():
            full_key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                result.update(self._flatten(v, full_key))
            else:
                result[full_key] = "***" if self._should_redact(full_key) else v
        return result

    def render(self, fmt: str = "table") -> str:
        if fmt not in self.SUPPORTED_FORMATS:
            raise RenderError(
                f"Unsupported format '{fmt}'. Choose from: {self.SUPPORTED_FORMATS}"
            )
        flat = self._flatten(self._config)
        if fmt == "table":
            return self._render_table(flat)
        elif fmt == "json":
            return json.dumps(flat, indent=2, default=str)
        elif fmt == "ini":
            return self._render_ini(flat)
        elif fmt == "shell":
            return self._render_shell(flat)

    def _render_table(self, flat: Dict[str, Any]) -> str:
        if not flat:
            return "(empty config)"
        col_width = max(len(k) for k in flat) + 2
        lines = [f"{'KEY':<{col_width}}  VALUE", "-" * (col_width + 20)]
        for k, v in sorted(flat.items()):
            lines.append(f"{k:<{col_width}}  {v}")
        return "\n".join(lines)

    def _render_ini(self, flat: Dict[str, Any]) -> str:
        lines = []
        for k, v in sorted(flat.items()):
            lines.append(f"{k} = {v}")
        return "\n".join(lines)

    def _render_shell(self, flat: Dict[str, Any]) -> str:
        lines = []
        for k, v in sorted(flat.items()):
            env_key = k.upper().replace(".", "_")
            lines.append(f"export {env_key}=\"{v}\"")
        return "\n".join(lines)
