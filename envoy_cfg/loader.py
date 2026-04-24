"""Config loader with layered environment support."""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

from .schema import Schema


DEFAULT_ENV_VAR = "APP_ENV"
DEFAULT_CONFIG_DIR = "config"


class ConfigLoader:
    """Loads layered config files: base -> environment-specific -> env var overrides."""

    def __init__(
        self,
        config_dir: str = DEFAULT_CONFIG_DIR,
        env: Optional[str] = None,
        env_var: str = DEFAULT_ENV_VAR,
        schema: Optional[Schema] = None,
    ):
        self.config_dir = Path(config_dir)
        self.env = env or os.environ.get(env_var, "development")
        self.schema = schema
        self._config: Dict[str, Any] = {}

    def _load_file(self, path: Path) -> Dict[str, Any]:
        """Load a JSON or YAML config file."""
        if not path.exists():
            return {}
        with open(path, "r") as f:
            if path.suffix in (".yaml", ".yml"):
                if not HAS_YAML:
                    raise ImportError("PyYAML is required to load .yaml files. Run: pip install pyyaml")
                return yaml.safe_load(f) or {}
            elif path.suffix == ".json":
                return json.load(f)
            else:
                raise ValueError(f"Unsupported config file format: {path.suffix}")

    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Override config values with environment variables (e.g. APP_DB_HOST -> db.host)."""
        prefix = "APP_"
        for key, value in os.environ.items():
            if key.startswith(prefix):
                parts = key[len(prefix):].lower().split("_")
                nested_key = ".".join(parts)
                config[nested_key] = value
        return config

    def load(self) -> Dict[str, Any]:
        """Load and merge configs: base -> env-specific -> environment variable overrides."""
        base_config = {}
        for ext in ("json", "yaml", "yml"):
            base_path = self.config_dir / f"base.{ext}"
            loaded = self._load_file(base_path)
            if loaded:
                base_config = loaded
                break

        env_config = {}
        for ext in ("json", "yaml", "yml"):
            env_path = self.config_dir / f"{self.env}.{ext}"
            loaded = self._load_file(env_path)
            if loaded:
                env_config = loaded
                break

        merged = {**base_config, **env_config}
        merged = self._apply_env_overrides(merged)

        if self.schema:
            merged = self.schema.validate(merged)

        self._config = merged
        return self._config

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a config value by key."""
        return self._config.get(key, default)

    @property
    def config(self) -> Dict[str, Any]:
        return self._config
