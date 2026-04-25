"""Tests for the ConfigRedactor module."""

import pytest
from envoy_cfg.redactor import ConfigRedactor, REDACTED_PLACEHOLDER


@pytest.fixture
def redactor() -> ConfigRedactor:
    return ConfigRedactor()


def test_non_sensitive_key_unchanged(redactor):
    config = {"host": "localhost", "port": 5432}
    result = redactor.redact(config)
    assert result == {"host": "localhost", "port": 5432}


def test_password_key_redacted(redactor):
    config = {"db_password": "supersecret"}
    result = redactor.redact(config)
    assert result["db_password"] == REDACTED_PLACEHOLDER


def test_token_key_redacted(redactor):
    config = {"access_token": "abc123"}
    result = redactor.redact(config)
    assert result["access_token"] == REDACTED_PLACEHOLDER


def test_api_key_redacted(redactor):
    config = {"api_key": "key-xyz"}
    result = redactor.redact(config)
    assert result["api_key"] == REDACTED_PLACEHOLDER


def test_nested_sensitive_key_redacted(redactor):
    config = {"database": {"host": "db.local", "password": "s3cr3t"}}
    result = redactor.redact(config)
    assert result["database"]["host"] == "db.local"
    assert result["database"]["password"] == REDACTED_PLACEHOLDER


def test_original_config_not_mutated(redactor):
    config = {"secret": "do-not-touch"}
    original = dict(config)
    redactor.redact(config)
    assert config == original


def test_custom_placeholder():
    r = ConfigRedactor(placeholder="[hidden]")
    result = r.redact({"password": "oops"})
    assert result["password"] == "[hidden]"


def test_extra_pattern_registered():
    r = ConfigRedactor(extra_patterns=["ssn"])
    result = r.redact({"user_ssn": "123-45-6789", "name": "Alice"})
    assert result["user_ssn"] == REDACTED_PLACEHOLDER
    assert result["name"] == "Alice"


def test_add_pattern_at_runtime(redactor):
    redactor.add_pattern("credit_card")
    result = redactor.redact({"credit_card_number": "4111111111111111"})
    assert result["credit_card_number"] == REDACTED_PLACEHOLDER


def test_deeply_nested_redaction(redactor):
    config = {"level1": {"level2": {"auth_token": "tok", "value": 42}}}
    result = redactor.redact(config)
    assert result["level1"]["level2"]["auth_token"] == REDACTED_PLACEHOLDER
    assert result["level1"]["level2"]["value"] == 42


def test_case_insensitive_match(redactor):
    config = {"DB_PASSWORD": "hidden", "MySecretKey": "also_hidden"}
    result = redactor.redact(config)
    assert result["DB_PASSWORD"] == REDACTED_PLACEHOLDER
    assert result["MySecretKey"] == REDACTED_PLACEHOLDER
