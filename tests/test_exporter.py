"""Tests for ConfigExporter."""

import json
import pytest
from envoy_cfg.exporter import ConfigExporter


@pytest.fixture
def sample_config():
    return {
        "debug": False,
        "host": "localhost",
        "port": 8080,
        "workers": 4,
        "db_url": "postgres://user:pass@localhost/db",
    }


def test_to_dict_returns_copy(sample_config):
    exporter = ConfigExporter(sample_config)
    result = exporter.to_dict()
    assert result == sample_config
    # Ensure it's a copy, not the same object
    result["extra"] = "value"
    assert "extra" not in exporter.to_dict()


def test_to_json_valid(sample_config):
    exporter = ConfigExporter(sample_config)
    result = exporter.to_json()
    parsed = json.loads(result)
    assert parsed["host"] == "localhost"
    assert parsed["port"] == 8080
    assert parsed["debug"] is False


def test_to_json_indent(sample_config):
    exporter = ConfigExporter(sample_config)
    result = exporter.to_json(indent=4)
    # 4-space indent means lines start with 4 spaces
    assert "    " in result


def test_to_dotenv_keys_uppercased(sample_config):
    exporter = ConfigExporter(sample_config)
    result = exporter.to_dotenv()
    assert "HOST=localhost" in result
    assert "PORT=8080" in result
    assert "DEBUG=False" in result


def test_to_dotenv_with_prefix(sample_config):
    exporter = ConfigExporter(sample_config)
    result = exporter.to_dotenv(prefix="APP")
    assert "APP_HOST=localhost" in result
    assert "APP_PORT=8080" in result


def test_to_dotenv_quotes_values_with_spaces():
    exporter = ConfigExporter({"greeting": "hello world"})
    result = exporter.to_dotenv()
    assert 'GREETING="hello world"' in result


def test_to_yaml_basic(sample_config):
    exporter = ConfigExporter(sample_config)
    result = exporter.to_yaml()
    assert 'host: "localhost"' in result
    assert "port: 8080" in result
    assert "debug: false" in result


def test_to_yaml_bool_lowercase():
    exporter = ConfigExporter({"enabled": True, "verbose": False})
    result = exporter.to_yaml()
    assert "enabled: true" in result
    assert "verbose: false" in result


def test_empty_config():
    exporter = ConfigExporter({})
    assert exporter.to_dict() == {}
    assert exporter.to_json() == "{}"
    assert exporter.to_dotenv() == ""
    assert exporter.to_yaml() == ""
