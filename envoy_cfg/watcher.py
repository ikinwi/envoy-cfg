"""File watcher for envoy-cfg.

Provides a ConfigWatcher class that monitors config files for changes
and triggers a reload callback when modifications are detected.
Useful for long-running services that need to pick up config changes
without restarting.
"""

import os
import time
import threading
import logging
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ConfigWatcher:
    """Watches a set of config files and calls a callback on changes.

    Uses a background thread with periodic polling to detect file
    modifications based on mtime. This avoids platform-specific
    filesystem event dependencies.

    Example usage::

        loader = ConfigLoader(config_dir="configs", env="production")
        config = loader.load()

        def on_change(updated_config):
            print("Config reloaded:", updated_config)

        watcher = ConfigWatcher(loader, on_change=on_change, interval=5)
        watcher.start()
        # ... run your app ...
        watcher.stop()
    """

    def __init__(
        self,
        loader,
        on_change: Optional[Callable[[Dict], None]] = None,
        interval: float = 5.0,
    ):
        """
        Args:
            loader: A ConfigLoader instance used to reload config.
            on_change: Callback invoked with the new config dict when a
                       change is detected. If None, changes are only logged.
            interval: Polling interval in seconds (default: 5.0).
        """
        self._loader = loader
        self._on_change = on_change
        self._interval = interval
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._mtimes: Dict[str, float] = {}

    def _get_watched_paths(self) -> List[str]:
        """Return list of config file paths currently tracked by the loader."""
        paths = []
        config_dir = self._loader.config_dir
        env = self._loader.env

        candidates = [
            os.path.join(config_dir, "base.yaml"),
            os.path.join(config_dir, "base.yml"),
            os.path.join(config_dir, f"{env}.yaml"),
            os.path.join(config_dir, f"{env}.yml"),
        ]
        for path in candidates:
            if os.path.isfile(path):
                paths.append(path)
        return paths

    def _snapshot_mtimes(self) -> Dict[str, float]:
        """Capture current modification times for all watched files."""
        return {
            path: os.path.getmtime(path)
            for path in self._get_watched_paths()
        }

    def _has_changed(self, current: Dict[str, float]) -> bool:
        """Compare current mtimes against the last known snapshot."""
        if set(current.keys()) != set(self._mtimes.keys()):
            return True
        return any(
            current.get(path) != self._mtimes.get(path)
            for path in current
        )

    def _watch_loop(self) -> None:
        """Background polling loop."""
        self._mtimes = self._snapshot_mtimes()
        logger.debug("ConfigWatcher started. Watching: %s", list(self._mtimes.keys()))

        while not self._stop_event.wait(self._interval):
            current = self._snapshot_mtimes()
            if self._has_changed(current):
                logger.info("Config change detected. Reloading...")
                self._mtimes = current
                try:
                    new_config = self._loader.load()
                    if self._on_change:
                        self._on_change(new_config)
                    else:
                        logger.info("Config reloaded (no callback registered).")
                except Exception as exc:  # pylint: disable=broad-except
                    logger.error("Failed to reload config: %s", exc)

    def start(self) -> None:
        """Start the background watcher thread."""
        if self._thread and self._thread.is_alive():
            logger.warning("ConfigWatcher is already running.")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._watch_loop,
            name="envoy-cfg-watcher",
            daemon=True,
        )
        self._thread.start()
        logger.debug("ConfigWatcher thread started.")

    def stop(self) -> None:
        """Stop the background watcher thread."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=self._interval + 1)
            self._thread = None
        logger.debug("ConfigWatcher stopped.")

    @property
    def is_running(self) -> bool:
        """True if the watcher thread is currently active."""
        return self._thread is not None and self._thread.is_alive()
