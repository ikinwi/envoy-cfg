"""Tests for envoy_cfg.merger module."""

import pytest
from envoy_cfg.merger import deep_merge, ConfigMerger


# ---------------------------------------------------------------------------
# deep_merge tests
# ---------------------------------------------------------------------------

def test_deep_merge_simple_override():
    base = {"host": "localhost", "port": 5432}
    override = {"port": 9999}
    result = deep_merge(base, override)
    assert result == {"host": "localhost", "port": 9999}


def test_deep_merge_adds_new_keys():
    base = {"host": "localhost"}
    override = {"debug": True}
    result = deep_merge(base, override)
    assert result["debug"] is True
    assert result["host"] == "localhost"


def test_deep_merge_nested_dicts():
    base = {"db": {"host": "localhost", "port": 5432, "name": "mydb"}}
    override = {"db": {"port": 9999}}
    result = deep_merge(base, override)
    assert result["db"] == {"host": "localhost", "port": 9999, "name": "mydb"}


def test_deep_merge_nested_override_replaces_scalar():
    base = {"db": "sqlite"}
    override = {"db": {"host": "pg"}}
    result = deep_merge(base, override)
    assert result["db"] == {"host": "pg"}


def test_deep_merge_does_not_mutate_inputs():
    base = {"a": {"x": 1}}
    override = {"a": {"y": 2}}
    deep_merge(base, override)
    assert "y" not in base["a"]
    assert "x" not in override["a"]


def test_deep_merge_empty_override():
    base = {"key": "value"}
    result = deep_merge(base, {})
    assert result == base


def test_deep_merge_empty_base():
    override = {"key": "value"}
    result = deep_merge({}, override)
    assert result == override


# ---------------------------------------------------------------------------
# ConfigMerger tests
# ---------------------------------------------------------------------------

def test_merger_no_layers_returns_empty():
    merger = ConfigMerger()
    assert merger.merge() == {}


def test_merger_single_layer():
    merger = ConfigMerger([{"host": "localhost"}])
    assert merger.merge() == {"host": "localhost"}


def test_merger_multiple_layers_priority():
    base = {"host": "localhost", "port": 80, "debug": False}
    staging = {"host": "staging.example.com", "debug": True}
    overrides = {"port": 443}

    merger = ConfigMerger([base, staging, overrides])
    result = merger.merge()

    assert result["host"] == "staging.example.com"
    assert result["port"] == 443
    assert result["debug"] is True


def test_merger_add_layer_chaining():
    merger = ConfigMerger()
    result = (
        merger
        .add_layer({"a": 1})
        .add_layer({"b": 2})
        .add_layer({"a": 99})
        .merge()
    )
    assert result == {"a": 99, "b": 2}


def test_merger_layer_count():
    merger = ConfigMerger([{"x": 1}, {"y": 2}])
    assert merger.layer_count == 2
    merger.add_layer({"z": 3})
    assert merger.layer_count == 3
