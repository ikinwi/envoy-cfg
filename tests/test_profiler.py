"""Tests for envoy_cfg.profiler."""

import pytest

from envoy_cfg.profiler import ConfigProfiler, ProfileReport, _flatten_keys


# ---------------------------------------------------------------------------
# _flatten_keys helpers
# ---------------------------------------------------------------------------

def test_flatten_keys_simple():
    result = _flatten_keys({"a": 1, "b": 2})
    assert result == {"a", "b"}


def test_flatten_keys_nested():
    result = _flatten_keys({"db": {"host": "localhost", "port": 5432}})
    assert "db" in result
    assert "db.host" in result
    assert "db.port" in result


def test_flatten_keys_deeply_nested():
    cfg = {"a": {"b": {"c": 42}}}
    result = _flatten_keys(cfg)
    assert "a.b.c" in result


# ---------------------------------------------------------------------------
# ProfileReport
# ---------------------------------------------------------------------------

def test_profile_report_has_issues_false_when_empty():
    report = ProfileReport()
    assert not report.has_issues


def test_profile_report_has_issues_true_when_unused():
    report = ProfileReport(unused_keys=["db.port"])
    assert report.has_issues


def test_profile_report_summary_no_issues():
    report = ProfileReport()
    assert "No issues found" in report.summary()


def test_profile_report_summary_lists_problems():
    report = ProfileReport(unused_keys=["x"], deprecated_keys=["old_key"])
    summary = report.summary()
    assert "Unused" in summary
    assert "Deprecated" in summary


# ---------------------------------------------------------------------------
# ConfigProfiler
# ---------------------------------------------------------------------------

@pytest.fixture()
def profiler():
    return ConfigProfiler(
        schema_keys={"host", "port", "debug", "db.name"},
        deprecated_keys=["old_timeout", "legacy_mode"],
    )


def test_no_issues_when_all_keys_present(profiler):
    cfg = {"host": "localhost", "port": 8080, "debug": False, "db": {"name": "mydb"}}
    report = profiler.profile(cfg)
    assert not report.unused_keys
    assert not report.deprecated_keys
    assert not report.duplicate_keys


def test_detects_unused_schema_keys(profiler):
    cfg = {"host": "localhost"}  # missing port, debug, db.name
    report = profiler.profile(cfg)
    assert "port" in report.unused_keys
    assert "debug" in report.unused_keys
    assert "db.name" in report.unused_keys


def test_detects_deprecated_keys(profiler):
    cfg = {"host": "x", "port": 1, "debug": True, "db": {"name": "y"}, "legacy_mode": True}
    report = profiler.profile(cfg)
    assert "legacy_mode" in report.deprecated_keys
    assert "old_timeout" not in report.deprecated_keys


def test_no_deprecated_when_keys_absent(profiler):
    cfg = {"host": "x", "port": 1, "debug": True, "db": {"name": "y"}}
    report = profiler.profile(cfg)
    assert not report.deprecated_keys


def test_no_schema_means_no_unused_keys():
    profiler = ConfigProfiler()
    cfg = {"anything": "goes"}
    report = profiler.profile(cfg)
    assert not report.unused_keys


def test_has_issues_false_for_clean_config(profiler):
    cfg = {"host": "h", "port": 9, "debug": False, "db": {"name": "d"}}
    report = profiler.profile(cfg)
    assert not report.has_issues
