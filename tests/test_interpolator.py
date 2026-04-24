"""Tests for envoy_cfg.interpolator module."""

import pytest
from envoy_cfg.interpolator import interpolate_value, interpolate_config


def test_interpolate_value_no_placeholders():
    assert interpolate_value("hello world", {}) == "hello world"


def test_interpolate_value_simple_substitution():
    context = {"host": "localhost"}
    assert interpolate_value("${host}", context) == "localhost"


def test_interpolate_value_with_default_present():
    context = {"port": "5432"}
    assert interpolate_value("${port:-3306}", context) == "5432"


def test_interpolate_value_with_default_missing():
    assert interpolate_value("${port:-3306}", {}) == "3306"


def test_interpolate_value_missing_key_no_default_raises():
    with pytest.raises(KeyError, match="host"):
        interpolate_value("${host}", {})


def test_interpolate_value_non_string_passthrough():
    assert interpolate_value(42, {"x": "y"}) == 42
    assert interpolate_value(None, {}) is None
    assert interpolate_value(["a", "b"], {}) == ["a", "b"]


def test_interpolate_value_inline_text():
    context = {"env": "production"}
    assert interpolate_value("app-${env}-v1", context) == "app-production-v1"


def test_interpolate_value_multiple_placeholders():
    context = {"host": "db.local", "port": "5432"}
    result = interpolate_value("${host}:${port}", context)
    assert result == "db.local:5432"


def test_interpolate_config_simple():
    config = {"db_url": "postgres://${host}:${port}/mydb", "host": "localhost", "port": "5432"}
    result = interpolate_config(config)
    assert result["db_url"] == "postgres://localhost:5432/mydb"


def test_interpolate_config_nested():
    config = {
        "app_name": "envoy",
        "database": {
            "name": "${app_name}_db"
        }
    }
    result = interpolate_config(config)
    assert result["database"]["name"] == "envoy_db"


def test_interpolate_config_does_not_mutate_original():
    config = {"key": "${missing:-fallback}"}
    original = dict(config)
    interpolate_config(config)
    assert config == original


def test_interpolate_config_list_values():
    config = {"env": "staging", "hosts": ["${env}-host1", "${env}-host2"]}
    result = interpolate_config(config)
    assert result["hosts"] == ["staging-host1", "staging-host2"]


def test_interpolate_config_custom_context():
    config = {"greeting": "Hello, ${name}!"}
    context = {"name": "World"}
    result = interpolate_config(config, context=context)
    assert result["greeting"] == "Hello, World!"
