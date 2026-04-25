"""Tests for ConfigRenderer."""

import json
import pytest
from envoy_cfg.renderer import ConfigRenderer, RenderError


@pytest.fixture
def flat_config():
    return {"host": "localhost", "port": 5432, "debug": True}


@pytest.fixture
def nested_config():
    return {
        "database": {"host": "db.local", "port": 5432},
        "app": {"name": "envoy", "secret_key": "abc123"},
    }


def test_render_table_contains_keys(flat_config):
    renderer = ConfigRenderer(flat_config)
    output = renderer.render("table")
    assert "host" in output
    assert "localhost" in output
    assert "port" in output


def test_render_table_sorted(flat_config):
    renderer = ConfigRenderer(flat_config)
    output = renderer.render("table")
    lines = [l for l in output.splitlines() if "=" not in l and "-" not in l and l.strip()]
    keys = [l.split()[0] for l in lines if not l.startswith("KEY")]
    assert keys == sorted(keys)


def test_render_json_valid(flat_config):
    renderer = ConfigRenderer(flat_config)
    output = renderer.render("json")
    parsed = json.loads(output)
    assert parsed["host"] == "localhost"
    assert parsed["port"] == 5432


def test_render_ini_format(flat_config):
    renderer = ConfigRenderer(flat_config)
    output = renderer.render("ini")
    assert "host = localhost" in output
    assert "port = 5432" in output


def test_render_shell_format(flat_config):
    renderer = ConfigRenderer(flat_config)
    output = renderer.render("shell")
    assert 'export HOST="localhost"' in output
    assert 'export PORT="5432"' in output


def test_unsupported_format_raises(flat_config):
    renderer = ConfigRenderer(flat_config)
    with pytest.raises(RenderError, match="Unsupported format"):
        renderer.render("xml")


def test_nested_config_flattened(nested_config):
    renderer = ConfigRenderer(nested_config)
    output = renderer.render("ini")
    assert "database.host = db.local" in output
    assert "app.name = envoy" in output


def test_redact_sensitive_keys(nested_config):
    renderer = ConfigRenderer(nested_config, redact_keys=["secret"])
    output = renderer.render("ini")
    assert "***" in output
    assert "abc123" not in output


def test_redact_does_not_affect_other_keys(nested_config):
    renderer = ConfigRenderer(nested_config, redact_keys=["secret"])
    output = renderer.render("json")
    parsed = json.loads(output)
    assert parsed["database.host"] == "db.local"


def test_empty_config_table():
    renderer = ConfigRenderer({})
    output = renderer.render("table")
    assert "empty" in output.lower()


def test_shell_keys_use_underscores(nested_config):
    renderer = ConfigRenderer(nested_config)
    output = renderer.render("shell")
    assert "DATABASE_HOST" in output
    assert "APP_NAME" in output
