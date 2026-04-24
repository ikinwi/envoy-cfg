"""Tests for envoy_cfg.schema module."""

import pytest

from envoy_cfg.schema import Schema, SchemaField


@pytest.fixture
def simple_schema():
    return Schema(
        fields={
            "host": SchemaField(str, required=True),
            "port": SchemaField(int, required=True),
            "debug": SchemaField(bool, required=False, default=False),
            "timeout": SchemaField(float, required=False, default=30.0),
        }
    )


def test_valid_config(simple_schema):
    config = {"host": "localhost", "port": 8080, "debug": True, "timeout": 5.0}
    result = simple_schema.validate(config)
    assert result["host"] == "localhost"
    assert result["port"] == 8080
    assert result["debug"] is True
    assert result["timeout"] == 5.0


def test_defaults_applied(simple_schema):
    config = {"host": "localhost", "port": 3000}
    result = simple_schema.validate(config)
    assert result["debug"] is False
    assert result["timeout"] == 30.0


def test_type_coercion(simple_schema):
    config = {"host": "localhost", "port": "9090"}
    result = simple_schema.validate(config)
    assert result["port"] == 9090
    assert isinstance(result["port"], int)


def test_missing_required_field(simple_schema):
    with pytest.raises(ValueError, match="Required field 'host' is missing"):
        simple_schema.validate({"port": 8080})


def test_unknown_keys_raise(simple_schema):
    config = {"host": "localhost", "port": 8080, "extra_key": "oops"}
    with pytest.raises(ValueError, match="Unknown config keys: extra_key"):
        simple_schema.validate(config)


def test_invalid_type_raises(simple_schema):
    config = {"host": "localhost", "port": "not-a-number"}
    with pytest.raises(TypeError, match="Field 'port' expects int"):
        simple_schema.validate(config)


def test_unsupported_field_type_raises():
    with pytest.raises(TypeError, match="Unsupported field type"):
        SchemaField(set)


def test_schema_field_none_default_optional():
    field = SchemaField(str, required=False, default="fallback")
    assert field.validate(None, "key") == "fallback"
