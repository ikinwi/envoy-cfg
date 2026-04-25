"""Tests for envoy_cfg.snapshot."""

import time
import pytest
from envoy_cfg.snapshot import Snapshot, SnapshotStore


# ---------------------------------------------------------------------------
# Snapshot
# ---------------------------------------------------------------------------

def test_snapshot_stores_deep_copy():
    cfg = {"db": {"host": "localhost"}}
    snap = Snapshot(config=cfg)
    cfg["db"]["host"] = "mutated"
    assert snap.config["db"]["host"] == "localhost"


def test_snapshot_is_immutable():
    snap = Snapshot(config={"key": "value"})
    with pytest.raises(AttributeError):
        snap.label = "new-label"


def test_snapshot_timestamp_auto_set():
    before = time.time()
    snap = Snapshot(config={})
    after = time.time()
    assert before <= snap.timestamp <= after


def test_snapshot_label_optional():
    snap = Snapshot(config={"x": 1})
    assert snap.label is None


def test_snapshot_label_stored():
    snap = Snapshot(config={}, label="v1")
    assert snap.label == "v1"


# ---------------------------------------------------------------------------
# SnapshotStore
# ---------------------------------------------------------------------------

@pytest.fixture
def store():
    return SnapshotStore()


def test_store_initially_empty(store):
    assert len(store) == 0
    assert store.latest() is None
    assert store.previous() is None


def test_capture_adds_snapshot(store):
    store.capture({"a": 1})
    assert len(store) == 1


def test_latest_returns_most_recent(store):
    store.capture({"a": 1})
    store.capture({"a": 2})
    assert store.latest().config == {"a": 2}


def test_previous_returns_second_most_recent(store):
    store.capture({"a": 1})
    store.capture({"a": 2})
    assert store.previous().config == {"a": 1}


def test_previous_none_when_only_one(store):
    store.capture({"a": 1})
    assert store.previous() is None


def test_history_returns_all(store):
    store.capture({"a": 1})
    store.capture({"a": 2})
    h = store.history()
    assert len(h) == 2


def test_history_returns_copy(store):
    store.capture({"a": 1})
    h = store.history()
    h.clear()
    assert len(store) == 1


def test_max_history_evicts_oldest():
    store = SnapshotStore(max_history=3)
    for i in range(5):
        store.capture({"i": i})
    assert len(store) == 3
    assert store.history()[0].config == {"i": 2}


def test_clear_empties_store(store):
    store.capture({"a": 1})
    store.clear()
    assert len(store) == 0


def test_capture_returns_snapshot(store):
    snap = store.capture({"x": 42}, label="test")
    assert isinstance(snap, Snapshot)
    assert snap.label == "test"
    assert snap.config == {"x": 42}
