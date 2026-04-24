"""Tests for the ConfigLoader module."""

import json
import os
import pytest
from pathlib import Path

from envoy_cfg.loader import ConfigLoader
from envoy_cfg.schema import Schema, SchemaField


@pytest.fixture
def config_dir(tmp_path):
    """Create a temporary config directory with base and env-specific files."""
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir()

    base = {"debug": False, "database": "sqlite", "port": 8080}
    (cfg_dir / "base.json").write_text(json.dumps(base))

    dev = {"debug": True, "port": 5000}
    (cfg_dir / "development.json").write_text(json.dumps(dev))

    prod = {"database": "postgres", "port": 443}
    (cfg_dir / "production.json").write_text(json.dumps(prod))

    return cfg_dir


def test_loads_base_config(config_dir):
    loader = ConfigLoader(config_dir=str(config_dir), env="staging")
    config = loader.load()
    assert config["database"] == "sqlite"
    assert config["port"] == 8080


def test_env_overrides_base(config_dir):
    loader = ConfigLoader(config_dir=str(config_dir), env="development")
    config = loader.load()
    assert config["debug"] is True
    assert config["port"] == 5000
    assert config["database"] == "sqlite"  # not overridden in dev


def test_production_overrides(config_dir):
    loader = ConfigLoader(config_dir=str(config_dir), env="production")
    config = loader.load()
    assert config["database"] == "postgres"
    assert config["port"] == 443
    assert config["debug"] is False


def test_missing_env_file_falls_back_to_base(config_dir):
    loader = ConfigLoader(config_dir=str(config_dir), env="unknown_env")
    config = loader.load()
    assert config["database"] == "sqlite"


def test_env_var_override(config_dir, monkeypatch):
    monkeypatch.setenv("APP_PORT", "9999")
    loader = ConfigLoader(config_dir=str(config_dir), env="development")
    config = loader.load()
    assert config["port"] == "9999"  # env vars come as strings


def test_get_method(config_dir):
    loader = ConfigLoader(config_dir=str(config_dir), env="development")
    loader.load()
    assert loader.get("debug") is True
    assert loader.get("nonexistent", "fallback") == "fallback"


def test_load_with_schema(config_dir):
    schema = Schema(fields=[
        SchemaField(name="port", field_type=int, required=True),
        SchemaField(name="debug", field_type=bool, required=False, default=False),
    ])
    loader = ConfigLoader(config_dir=str(config_dir), env="development", schema=schema)
    config = loader.load()
    assert isinstance(config["port"], int)
    assert config["debug"] is True


def test_empty_config_dir(tmp_path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    loader = ConfigLoader(config_dir=str(empty_dir), env="development")
    config = loader.load()
    assert config == {}
