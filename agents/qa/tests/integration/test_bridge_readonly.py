"""Desktop Bridge integration — read-only surface over the sample OKF tree.

Exercises the ``window.pywebview.api`` contract (`hephaestus.desktop.Bridge`)
directly in Python, no browser and no live LLM calls. These methods run against
the shipped ``sample/`` tree read-only.

Run (from repo root)::

    agents/.venv/Scripts/python.exe -m pytest agents/qa/tests -q

Catalog cases covered: TC-DESK-001, TC-DESK-002, TC-DESK-006, TC-DESK-007,
TC-PROV-004, TC-CODE-001, TC-CODE-002, TC-CODE-003, TC-SEC-001, TC-SEC-002,
TC-MARK-001/003 (via the bridge), TC-MARK-009 (via the bridge).
"""
from __future__ import annotations

from pathlib import Path

import pytest


# --- Dashboard snapshot (TC-DESK-001 / F-4) ---------------------------------

def test_get_state_returns_snapshot_envelope(sample_bridge):
    state = sample_bridge.get_state()
    assert set(state) >= {"root", "issues", "violations", "workflow_canvas", "summary"}
    assert isinstance(state["issues"], list)          # empty until a workflow feeds it
    assert isinstance(state["violations"], list)
    assert set(state["summary"]) >= {"issues", "violations", "error", "warning", "info"}
    assert "available_nodes" in state["workflow_canvas"]


def test_rescan_matches_get_state_shape(sample_bridge):
    assert set(sample_bridge.rescan()) == set(sample_bridge.get_state())


# --- Catalog + rules (TC-PROV-004, TC-DESK-002) -----------------------------

def test_get_catalog_shape(sample_bridge):
    catalog = sample_bridge.get_catalog()
    assert "providers" in catalog
    assert isinstance(catalog["providers"], list) and catalog["providers"]
    provider = catalog["providers"][0]
    assert {"provider", "models"} <= set(provider)


def test_list_rules_returns_governance_layer(sample_bridge):
    rules = sample_bridge.list_rules()
    ids = {rule["id"] for rule in rules}
    assert {"G-001", "G-002", "G-003"} <= ids
    for rule in rules:
        assert {"id", "name", "severity", "fix_hint"} <= set(rule)


# --- Code viewer (TC-CODE-001/002/003) --------------------------------------

def test_list_repos_includes_sample(sample_bridge, sample_root):
    repos = {repo["name"] for repo in sample_bridge.list_repos()}
    assert sample_root.name in repos


def test_tree_lists_agents_dir_and_ignores_vcs(sample_bridge, sample_root):
    entries = sample_bridge.tree(sample_root.name)
    by_name = {entry["name"]: entry["type"] for entry in entries}
    assert by_name.get("agents") == "dir"
    assert ".git" not in by_name       # vcs/build dirs are filtered


def test_read_file_returns_language_and_content(sample_bridge, sample_root):
    result = sample_bridge.read_file(sample_root.name, "agents/identities/node-001.json")
    assert result["language"] == "json"
    assert result["binary"] is False and result["truncated"] is False
    assert result["content"].strip().startswith("{")


# --- Path-traversal security (TC-SEC-001 / TC-CODE-006, TC-SEC-002) ---------

def test_read_file_rejects_relative_escape(sample_bridge, sample_root):
    with pytest.raises(ValueError):
        sample_bridge.read_file(sample_root.name, "../../secret.txt")


def test_tree_rejects_relative_escape(sample_bridge, sample_root):
    with pytest.raises(ValueError):
        sample_bridge.tree(sample_root.name, "../")


def test_read_file_rejects_absolute_path_outside_root(sample_bridge, sample_root, repo_root):
    outside = str(repo_root / "pyproject.toml")   # real file, outside the repo root
    with pytest.raises(ValueError):
        sample_bridge.read_file(sample_root.name, outside)


# --- Pure marker parsing (TC-DESK-006 / TC-MARK-001/003) --------------------

def test_parse_handoff_marker_valid(sample_bridge):
    text = '@@HEPHAESTUS@@ {"v":1,"type":"handoff","role":"worker","task":"do it","issue_id":"issue-1"}'
    marker = sample_bridge.parse_handoff_marker(text)
    assert marker == {"role": "worker", "task": "do it", "issue_id": "issue-1"}


def test_parse_handoff_marker_malformed_returns_none(sample_bridge):
    assert sample_bridge.parse_handoff_marker("no marker here") is None
    # Missing required issue_id field -> not a valid handoff.
    assert sample_bridge.parse_handoff_marker(
        '@@HEPHAESTUS@@ {"v":1,"type":"handoff","role":"worker","task":"do it"}'
    ) is None


# --- Spawn gate (TC-DESK-007 / TC-MARK-009) ---------------------------------

def test_evaluate_spawn_green_with_no_exit_rules(sample_bridge):
    card = sample_bridge.evaluate_spawn("worker", "implement X", "issue-1")
    assert card["gating"] == "green"          # no exit rules -> nothing to fail
    assert card["prefill_role"] == "worker"
    assert card["prefill_task"] == "implement X"
    assert card["failures"] == []
