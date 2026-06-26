from __future__ import annotations

import json

from hephaestus.dashboard import snapshot


def test_clean_snapshot_has_no_violations(clean_tree):
    snap = snapshot(clean_tree)
    assert snap["summary"]["violations"] == 0
    assert snap["issues"] == []  # no workflow/node model feeds rows yet


def test_schema_error_surfaces_in_snapshot(schema_error_tree):
    snap = snapshot(schema_error_tree)
    assert snap["summary"]["violations"] >= 1
    assert any(v["rule_id"] == "schema" for v in snap["violations"])


def test_snapshot_is_json_serializable(schema_error_tree):
    json.dumps(snapshot(schema_error_tree))  # must not raise
