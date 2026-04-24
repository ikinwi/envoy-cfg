"""Tests for ConfigValidator."""

import pytest
from envoy_cfg.validator import ConfigValidator, ValidationError
from envoy_cfg.schema import Schema, SchemaField


@pytest.fixture()
def simple_schema():
    return Schema(
        fields={
            "host": SchemaField(type=str, required=True),
            "port": SchemaField(type=int, required=False, default=8080),
            "debug": SchemaField(type=bool, required=False, default=False),
        }
    )


def test_validate_returns_resolved_config(simple_schema):
    cfg = {"host": "localhost"}
    result = ConfigValidator(simple_schema).validate(cfg)
    assert result["host"] == "localhost"
    assert result["port"] == 8080


def test_validate_no_schema_passes_through():
    cfg = {"key": "value"}
    result = ConfigValidator().validate(cfg)
    assert result == {"key": "value"}


def test_validate_interpolation_resolved(simple_schema):
    cfg = {"host": "${base_host}", "port": 9000}
    context = {"base_host": "prod.example.com"}
    result = ConfigValidator(simple_schema).validate(cfg, context=context)
    assert result["host"] == "prod.example.com"


def test_validate_interpolation_self_reference():
    cfg = {"app": "myapp", "label": "${app}-service"}
    result = ConfigValidator().validate(cfg)
    assert result["label"] == "myapp-service"


def test_validate_missing_required_raises(simple_schema):
    with pytest.raises(ValidationError) as exc_info:
        ConfigValidator(simple_schema).validate({})
    assert "Schema error" in str(exc_info.value)
    assert len(exc_info.value.errors) >= 1


def test_validate_interpolation_missing_key_raises():
    cfg = {"url": "${undefined_var}"}
    with pytest.raises(ValidationError) as exc_info:
        ConfigValidator().validate(cfg)
    assert "Interpolation error" in str(exc_info.value)


def test_is_valid_true(simple_schema):
    assert ConfigValidator(simple_schema).is_valid({"host": "localhost"}) is True


def test_is_valid_false_missing_required(simple_schema):
    assert ConfigValidator(simple_schema).is_valid({}) is False


def test_is_valid_false_bad_interpolation():
    assert ConfigValidator().is_valid({"x": "${missing}"}) is False


def test_validation_error_message_lists_all_errors():
    err = ValidationError(["first problem", "second problem"])
    msg = str(err)
    assert "first problem" in msg
    assert "second problem" in msg
    assert "1." in msg
    assert "2." in msg
