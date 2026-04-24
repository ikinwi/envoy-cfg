"""Variable interpolation for config values.

Supports ${VAR_NAME} and ${VAR_NAME:-default} syntax within string values.
"""

import re
from typing import Any, Dict, Optional

_INTERPOLATION_RE = re.compile(r"\$\{([^}]+)\}")


def _resolve_token(token: str, context: Dict[str, Any]) -> str:
    """Resolve a single interpolation token like VAR_NAME or VAR_NAME:-default."""
    if ":-" in token:
        var_name, default_value = token.split(":-", 1)
    else:
        var_name, default_value = token, None

    var_name = var_name.strip()
    keys = var_name.split(".")

    value = context
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            value = None
            break

    if value is None or not isinstance(value, (str, int, float, bool)):
        if default_value is not None:
            return default_value
        raise KeyError(f"Interpolation key '{var_name}' not found and no default provided")

    return str(value)


def interpolate_value(value: Any, context: Dict[str, Any]) -> Any:
    """Interpolate a single value against the given context dict."""
    if not isinstance(value, str):
        return value

    def replacer(match: re.Match) -> str:
        return _resolve_token(match.group(1), context)

    return _INTERPOLATION_RE.sub(replacer, value)


def interpolate_config(config: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Recursively interpolate all string values in a config dict.

    Args:
        config: The configuration dictionary to process.
        context: The lookup context for variable resolution. Defaults to config itself.

    Returns:
        A new dictionary with all interpolations resolved.
    """
    if context is None:
        context = config

    result: Dict[str, Any] = {}
    for key, value in config.items():
        if isinstance(value, dict):
            result[key] = interpolate_config(value, context)
        elif isinstance(value, list):
            result[key] = [
                interpolate_value(item, context) if isinstance(item, str) else item
                for item in value
            ]
        else:
            result[key] = interpolate_value(value, context)
    return result
