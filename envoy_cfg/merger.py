"""Config layer merger for envoy-cfg.

Provides deep merging of configuration dictionaries across
multiple environment layers (base -> env-specific -> overrides).
"""

from typing import Any, Dict, List


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge override dict into base dict.

    Nested dicts are merged recursively. All other types are
    replaced by the override value.

    Args:
        base: The base configuration dictionary.
        override: Values to merge on top of base.

    Returns:
        A new merged dictionary (base and override are not mutated).
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class ConfigMerger:
    """Merges multiple configuration layers in order."""

    def __init__(self, layers: List[Dict[str, Any]] = None):
        """Initialize with an optional list of config layer dicts.

        Args:
            layers: Ordered list of config dicts, from lowest to highest priority.
        """
        self._layers: List[Dict[str, Any]] = layers if layers is not None else []

    def add_layer(self, layer: Dict[str, Any]) -> "ConfigMerger":
        """Append a new layer on top of existing layers.

        Args:
            layer: Config dict to add as the highest-priority layer.

        Returns:
            self, to allow chaining.
        """
        self._layers.append(layer)
        return self

    def merge(self) -> Dict[str, Any]:
        """Merge all layers and return the resulting config dict.

        Returns:
            A single merged configuration dictionary.
        """
        result: Dict[str, Any] = {}
        for layer in self._layers:
            result = deep_merge(result, layer)
        return result

    @property
    def layer_count(self) -> int:
        """Return the number of layers currently registered."""
        return len(self._layers)
