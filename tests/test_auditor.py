"""Tests for envoy_cfg.auditor."""

import pytest
from envoy_cfg.auditor import ConfigAuditor, ConfigDiff, AuditReport, _flatten


# ---------------------------------------------------------------------------
# _flatten helpers
# ---------------------------------------------------------------------------

def test_flatten_simple_dict():
    result = _flatten({"a": 1, "b": 2})
    assert result == {"a": 1, "b": 2}


def test_flatten_nested_dict():
    result = _flatten({"db": {"host": "localhost", "port": 5432}})
    assert result == {"db.host": "localhost", "db.port": 5432}


def test_flatten_deeply_nested():
    result = _flatten({"a": {"b": {"c": 42}}})
    assert result == {"a.b.c": 42}


# ---------------------------------------------------------------------------
# ConfigAuditor.diff
# ---------------------------------------------------------------------------

@pytest.fixture
def auditor():
    return ConfigAuditor()


def test_no_changes(auditor):
    cfg = {"debug": True, "db": {"host": "localhost"}}
    report = auditor.diff(cfg, cfg)
    assert not report.has_changes
    assert report.summary() == "AuditReport: 0 added, 0 removed, 0 modified"


def test_added_key(auditor):
    old = {"debug": True}
    new = {"debug": True, "log_level": "info"}
    report = auditor.diff(old, new)
    assert report.has_changes
    assert len(report.added) == 1
    assert report.added[0].key == "log_level"
    assert report.added[0].new_value == "info"
    assert report.added[0].old_value is None


def test_removed_key(auditor):
    old = {"debug": True, "legacy": "value"}
    new = {"debug": True}
    report = auditor.diff(old, new)
    assert len(report.removed) == 1
    assert report.removed[0].key == "legacy"
    assert report.removed[0].new_value is None


def test_modified_key(auditor):
    old = {"debug": False}
    new = {"debug": True}
    report = auditor.diff(old, new)
    assert len(report.modified) == 1
    assert report.modified[0].old_value is False
    assert report.modified[0].new_value is True


def test_nested_modified_key(auditor):
    old = {"db": {"host": "localhost", "port": 5432}}
    new = {"db": {"host": "prod-db", "port": 5432}}
    report = auditor.diff(old, new)
    assert len(report.modified) == 1
    assert report.modified[0].key == "db.host"


def test_mixed_changes(auditor):
    old = {"a": 1, "b": 2, "c": 3}
    new = {"a": 99, "b": 2, "d": 4}
    report = auditor.diff(old, new)
    assert len(report.added) == 1    # d
    assert len(report.removed) == 1  # c
    assert len(report.modified) == 1 # a


def test_config_diff_repr():
    d = ConfigDiff("db.host", "localhost", "prod", "modified")
    assert "modified" in repr(d)
    assert "db.host" in repr(d)


def test_audit_report_summary_counts():
    diffs = [
        ConfigDiff("x", None, 1, "added"),
        ConfigDiff("y", 2, None, "removed"),
        ConfigDiff("z", 3, 4, "modified"),
    ]
    report = AuditReport(diffs=diffs)
    assert "1 added" in report.summary()
    assert "1 removed" in report.summary()
    assert "1 modified" in report.summary()
